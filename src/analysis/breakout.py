"""
Breakout 策略 - 唯一策略逻辑（Single Source of Truth）

职责：
- 计算所有技术指标（BB, RSI, EMA20, SPY SMA200, VIX）
- 生成买入和卖出信号
- 作为回测和实盘的统一逻辑
"""
import pandas as pd
import numpy as np


def add_signals_to_dataframe(df, spy_df=None, vix_df=None):
    """
    为股票 DataFrame 添加所有指标和信号
    
    Args:
        df: 股票价格数据 (columns: open, high, low, close, volume)
        spy_df: SPY 数据（用于市场环境过滤）
        vix_df: VIX 数据（用于市场环境过滤）
        
    Returns:
        DataFrame with additional columns:
        - bb_upper, bb_middle, bb_lower (布林带)
        - rsi (RSI)
        - ema20 (20日均线)
        - Buy_Signal (买入信号)
        - Sell_Signal (卖出信号 - 仅移动止损)
    """
    # 确保索引是 datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # 确保列名是小写
    df.columns = [str(col).lower() for col in df.columns]
    
    # ============================================================================
    # 计算技术指标
    # ============================================================================
    
    # 1. EMA20 (20日指数移动平均线)
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    
    # 2. 布林带 (20日, 2标准差)
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    df['bb_std'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
    
    # 3. RSI (14日相对强弱指标)
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    df['rsi'] = calculate_rsi(df['close'], period=14)
    
    # ============================================================================
    # 计算市场环境过滤器
    # ============================================================================
    
    # 初始化市场过滤器为 True（允许交易）
    market_filter = pd.Series(True, index=df.index)
    
    # SPY 过滤器：SPY Close > SMA200 (牛市环境)
    if spy_df is not None and not spy_df.empty:
        if not isinstance(spy_df.index, pd.DatetimeIndex):
            spy_df.index = pd.to_datetime(spy_df.index)
        spy_df.columns = [str(col).lower() for col in spy_df.columns]
        
        spy_sma200 = spy_df['close'].rolling(window=200).mean()
        spy_bullish = spy_df['close'] > spy_sma200
        
        # 对齐到股票的日期索引
        spy_bullish_aligned = spy_bullish.reindex(df.index, method='ffill')
        market_filter = market_filter & spy_bullish_aligned.fillna(True)
    
    # VIX 过滤器：VIX < 30 (低风险环境)
    if vix_df is not None and not vix_df.empty:
        if not isinstance(vix_df.index, pd.DatetimeIndex):
            vix_df.index = pd.to_datetime(vix_df.index)
        vix_df.columns = [str(col).lower() for col in vix_df.columns]
        
        vix_low_risk = vix_df['close'] < 30
        
        # 对齐到股票的日期索引
        vix_low_risk_aligned = vix_low_risk.reindex(df.index, method='ffill')
        market_filter = market_filter & vix_low_risk_aligned.fillna(True)
    
    # ============================================================================
    # 生成信号
    # ============================================================================
    
    # 买入信号：Close > BB Upper AND 60 < RSI < 80 AND 市场过滤器
    df['Buy_Signal'] = (
        (df['close'] > df['bb_upper']) &
        (df['rsi'] > 60) &
        (df['rsi'] < 80) &
        market_filter
    )
    
    # 卖出信号：Close < EMA20 (移动止损)
    # 注意：硬止损（-5%）由回测引擎动态计算，因为需要知道实际入场价格
    df['Sell_Signal'] = (df['close'] < df['ema20'])
    
    # 清理中间计算列
    df = df.drop(['bb_std'], axis=1, errors='ignore')
    
    return df


def calculate_indicators_batch(data_dict, spy_df=None, vix_df=None):
    """
    批量为多只股票添加指标和信号
    
    Args:
        data_dict: {ticker: DataFrame} 字典
        spy_df: SPY 数据
        vix_df: VIX 数据
        
    Returns:
        {ticker: DataFrame} 字典，每个 DataFrame 包含信号
    """
    result = {}
    
    for ticker, df in data_dict.items():
        try:
            df_with_signals = add_signals_to_dataframe(df.copy(), spy_df, vix_df)
            result[ticker] = df_with_signals
        except Exception as e:
            print(f"Error adding signals to {ticker}: {e}")
            continue
    
    return result


def get_today_signals(df, date=None):
    """
    获取指定日期的买入信号
    
    Args:
        df: 包含信号的 DataFrame
        date: 日期 (默认为最新日期)
        
    Returns:
        DataFrame: 当天的信号数据
    """
    if date is None:
        date = df.index[-1]
    
    # 确保日期在数据中
    if date not in df.index:
        # 找到最近的日期
        available_dates = df.index[df.index <= date]
        if len(available_dates) > 0:
            date = available_dates[-1]
        else:
            return pd.DataFrame()
    
    # 返回当天的数据
    return df.loc[[date]]