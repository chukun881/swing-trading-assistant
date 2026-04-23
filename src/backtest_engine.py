"""
Swing Trading Assistant - 回测引擎
使用 backtrader 库进行策略回测
"""
import backtrader as bt
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import logging
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# IBKR 佣金计算类（Tiered Pricing）
# ============================================================================

class IBKRCommission(bt.CommissionInfo):
    """
    IBKR Tiered Pricing 佣金计算
    
    规则：
    - $0.0035 per share
    - Minimum $0.35 per trade
    - Maximum 1% of total trade value
    """
    params = (
        ('per_share', 0.0035),
        ('minimum', 0.35),
        ('max_pct', 0.01),
    )
    
    def _getcommission(self, size, price, pseudoexec):
        """计算佣金"""
        # 计算交易价值
        trade_value = abs(size) * price
        
        # 方法1：按股数计算
        commission_by_share = abs(size) * self.p.per_share
        
        # 方法2：按百分比计算（上限）
        commission_by_pct = trade_value * self.p.max_pct
        
        # 取最小值（方法1和上限中较小的）
        commission = min(commission_by_share, commission_by_pct)
        
        # 应用最低收费
        commission = max(commission, self.p.minimum)
        
        return commission


# ============================================================================
# 指标类
# ============================================================================

class EMA(bt.indicators.EMA):
    """指数移动平均线"""
    pass


class RSI(bt.indicators.RSI):
    """相对强弱指标"""
    pass


class BollingerBands(bt.indicators.BollingerBands):
    """布林带"""
    pass


class VolumeSMA(bt.indicators.SMA):
    """成交量移动平均线"""
    pass


# ============================================================================
# 自定义指标
# ============================================================================

class CandlestickPattern(bt.Indicator):
    """
    K线形态检测
    
    检测形态：
    - 锤子线 (Hammer)
    - 十字星 (Doji)
    - 吞没阳线 (Bullish Engulfing)
    """
    lines = ('hammer', 'doji', 'bullish_engulfing')
    params = (
        ('hammer_body_ratio', 0.3),      # 实体占影线比例
        ('doji_body_ratio', 0.1),        # 十字星实体比例
    )
    plotinfo = dict(plot=False)
    
    def __init__(self):
        # 获取 OHLC 数据
        self.o = self.data.open
        self.h = self.data.high
        self.l = self.data.low
        self.c = self.data.close
        
        # 前一日数据
        self.o1 = self.data.open(-1)
        self.h1 = self.data.high(-1)
        self.l1 = self.data.low(-1)
        self.c1 = self.data.close(-1)
        
        # 计算实体和影线
        self.body = abs(self.c - self.o)
        self.range1 = self.h - self.l
        self.upper_shadow = bt.If(self.c >= self.o, self.h - self.o, self.h - self.c)
        self.lower_shadow = bt.If(self.c >= self.o, self.o - self.l, self.c - self.l)
        
        # 前一日实体
        self.body1 = abs(self.c1 - self.o1)
        
        # 锤子线：小实体 + 长下影线
        is_bullish = self.c >= self.o
        is_small_body = self.body <= self.range1 * self.p.hammer_body_ratio
        is_long_lower_shadow = self.lower_shadow >= self.range1 * 0.6
        is_short_upper_shadow = self.upper_shadow <= self.range1 * 0.2
        
        self.lines.hammer = bt.And(is_bullish, is_small_body, is_long_lower_shadow, is_short_upper_shadow)
        
        # 十字星：实体很小
        self.lines.doji = self.body <= self.range1 * self.p.doji_body_ratio
        
        # 吞没阳线：今日阳线完全包住昨日阴线
        is_bullish_today = self.c > self.o
        is_bearish_yesterday = self.c1 < self.o1
        is_engulf_high = self.c >= self.o1
        is_engulf_low = self.o <= self.c1
        
        self.lines.bullish_engulfing = bt.And(is_bullish_today, is_bearish_yesterday, is_engulf_high, is_engulf_low)


# ============================================================================
# 市场环境过滤器
# ============================================================================

class MarketRegime(bt.Indicator):
    """
    市场环境过滤器
    
    基于 VIX 判断市场环境：
    - VIX > 30：高风险，暂停信号
    - VIX <= 30：正常，允许信号
    """
    lines = ('vix', 'is_safe',)
    plotinfo = dict(plot=False)
    params = (('vix_threshold', 30.0),)
    
    def __init__(self):
        # VIX 需要从外部数据源获取
        # 这里我们会在 Cerebro 中添加 VIX 数据
        self.lines.vix = self.data.close  # 假设 data 是 VIX
        self.lines.is_safe = self.lines.vix <= self.p.vix_threshold


# ============================================================================
# 交易策略
# ============================================================================

class SwingTradingStrategy(bt.Strategy):
    """
    Swing Trading 策略
    
    整合 Breakout 和 Pullback 策略
    """
    params = (
        # 通用参数
        ('position_size', 0.10),  # 每次交易使用 10% 资金
        ('risk_per_trade', 0.02),  # 每次交易风险 2%
        
        # Breakout 参数
        ('breakout_rsi_min', 60),
        ('breakout_rsi_max', 75),
        ('breakout_volume_mult', 1.5),  # 成交量倍数
        
        # Pullback 参数
        ('pullback_rsi_oversold', 30),
        ('pullback_rsi_recovery', 0.5),
        
        # 市场环境
        ('vix_threshold', 30.0),
    )
    
    def __init__(self):
        # 指标
        self.ema20 = EMA(self.data, period=20)
        self.ema50 = EMA(self.data, period=50)
        self.rsi = RSI(self.data, period=14)
        self.bb = BollingerBands(self.data, period=20, devfactor=2.0)
        self.vol_sma20 = VolumeSMA(self.data.volume, period=20)
        
        # K线形态
        self.pattern = CandlestickPattern(self.data)
        
        # 市场环境（如果有 VIX 数据）
        self.is_safe = True
        if hasattr(self, 'vix_data'):
            self.vix = self.vix_data.close
            self.is_safe = self.vix <= self.p.vix_threshold
        else:
            logger.warning("No VIX data provided, proceeding without market filter")
        
        # 交易记录
        self.trades = []
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # 记录最大回撤
        self.max_equity = self.broker.getvalue()
        self.max_drawdown = 0.0
        
        # 跟踪当前持仓
        self.entry_price = None
        self.entry_date = None
        
    def next(self):
        """每个 bar 调用"""
        # 更新最大回撤
        current_equity = self.broker.getvalue()
        if current_equity > self.max_equity:
            self.max_equity = current_equity
        drawdown = (self.max_equity - current_equity) / self.max_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # 检查市场环境
        is_market_safe = self.is_safe[0] if hasattr(self.is_safe, '__getitem__') else self.is_safe
        if not is_market_safe:
            # 高风险环境，不产生新信号
            return
        
        # 如果已持有仓位，检查退出信号
        if self.position:
            self.check_exit_signals()
        else:
            # 检查入场信号
            self.check_entry_signals()
    
    def check_entry_signals(self):
        """检查入场信号"""
        # Breakout 策略
        breakout_signal = self.check_breakout()
        if breakout_signal:
            self.enter_position('BREAKOUT', breakout_signal)
            return
        
        # Pullback 策略
        pullback_signal = self.check_pullback()
        if pullback_signal:
            self.enter_position('PULLBACK', pullback_signal)
            return
    
    def check_breakout(self):
        """
        Breakout 策略
        
        条件：
        1. price > EMA50
        2. close > upper band
        3. 60 <= RSI <= 75
        4. volume > 20日平均成交量 × 1.5
        """
        close = self.data.close[0]
        ema50 = self.ema50[0]
        rsi = self.rsi[0]
        bb_upper = self.bb.top[0]
        volume = self.data.volume[0]
        vol_sma = self.vol_sma20[0]
        
        # 检查条件
        cond1 = close > ema50
        cond2 = close > bb_upper
        cond3 = self.p.breakout_rsi_min <= rsi <= self.p.breakout_rsi_max
        cond4 = volume > vol_sma * self.p.breakout_volume_mult
        
        if all([cond1, cond2, cond3, cond4]):
            signal_type = 'BUY'
            if rsi > (self.p.breakout_rsi_max - 5):  # RSI > 70
                signal_type = 'WAIT RETEST'
            
            return {
                'type': signal_type,
                'price': close,
                'rsi': rsi,
                'volume_ratio': volume / vol_sma,
            }
        
        return None
    
    def check_pullback(self):
        """
        Pullback 策略
        
        条件：
        1. price > EMA50
        2. EMA20 > EMA50
        3. price <= lower band
        4. RSI < 30
        5. RSI 正在回升
        6. 出现锤子线 / 十字星 / 吞没阳线（当日收红）
        """
        close = self.data.close[0]
        ema20 = self.ema20[0]
        ema50 = self.ema50[0]
        rsi = self.rsi[0]
        rsi_prev = self.rsi[-1]
        bb_lower = self.bb.bot[0]
        
        # 检查基础条件
        cond1 = close > ema50
        cond2 = ema20 > ema50
        cond3 = close <= bb_lower
        cond4 = rsi < self.p.pullback_rsi_oversold
        cond5 = (rsi - rsi_prev) >= self.p.pullback_rsi_recovery
        
        # 检查 K线形态
        is_bullish = close > self.data.open[0]
        has_hammer = self.pattern.hammer[0]
        has_doji = self.pattern.doji[0]
        has_engulfing = self.pattern.bullish_engulfing[0]
        cond6 = is_bullish and (has_hammer or has_doji or has_engulfing)
        
        if all([cond1, cond2, cond3, cond4, cond5, cond6]):
            return {
                'type': 'BUY',
                'price': close,
                'rsi': rsi,
                'pattern': 'Hammer' if has_hammer else ('Doji' if has_doji else 'Engulfing'),
            }
        
        return None
    
    def enter_position(self, strategy, signal):
        """入场"""
        if signal['type'] == 'WAIT RETEST':
            logger.info(f"{strategy}: Wait for retest at ${signal['price']:.2f}")
            return
        
        # 计算仓位大小
        equity = self.broker.getvalue()
        position_value = equity * self.p.position_size
        size = int(position_value / signal['price'])
        
        if size <= 0:
            logger.warning(f"Cannot open position: size={size}, price={signal['price']:.2f}")
            return
        
        # 开仓
        self.buy(size=size)
        self.entry_price = signal['price']
        self.entry_date = self.data.datetime.date(0)
        
        logger.info(f"ENTER {strategy}: {self.data._name} at ${signal['price']:.2f}, "
                   f"size={size}, RSI={signal['rsi']:.1f}")
    
    def check_exit_signals(self):
        """检查退出信号"""
        close = self.data.close[0]
        rsi = self.rsi[0]
        
        # 退出条件
        exit_reason = None
        
        # 1. 价格跌破 EMA20
        if close < self.ema20[0]:
            exit_reason = "Price < EMA20"
        
        # 2. RSI > 75（超买）
        elif rsi > 75:
            exit_reason = "RSI > 75 (Overbought)"
        
        # 3. 止损 -5%
        elif self.entry_price and close < self.entry_price * 0.95:
            exit_reason = "Stop Loss (-5%)"
        
        # 4. 止盈 +10%
        elif self.entry_price and close > self.entry_price * 1.10:
            exit_reason = "Take Profit (+10%)"
        
        if exit_reason:
            self.close_position(exit_reason)
    
    def close_position(self, reason):
        """平仓"""
        current_price = self.data.close[0]
        
        # 记录交易
        pnl = (current_price - self.entry_price) / self.entry_price
        
        trade_info = {
            'symbol': self.data._name,
            'entry_date': self.entry_date,
            'exit_date': self.data.datetime.date(0),
            'entry_price': self.entry_price,
            'exit_price': current_price,
            'pnl_pct': pnl,
            'reason': reason,
        }
        self.trades.append(trade_info)
        
        # 统计
        self.trade_count += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        logger.info(f"EXIT {self.data._name} at ${current_price:.2f}, "
                   f"PnL={pnl*100:+.2f}%, Reason={reason}")
        
        # 平仓
        self.close()
        self.entry_price = None
        self.entry_date = None
    
    def stop(self):
        """回测结束时调用"""
        final_value = self.broker.getvalue()
        initial_value = 10000.0
        total_return = (final_value - initial_value) / initial_value * 100
        
        win_rate = 0
        if self.trade_count > 0:
            win_rate = self.winning_trades / self.trade_count * 100
        
        max_dd = self.max_drawdown * 100
        
        # 打印结果
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:+.2f}%")
        print(f"Total Trades: {self.trade_count}")
        print(f"Winning Trades: {self.winning_trades}")
        print(f"Losing Trades: {self.losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Maximum Drawdown: {max_dd:.2f}%")
        print("=" * 60)
        
        # 保存交易记录
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv('backtest_trades.csv', index=False)
            logger.info(f"Trade history saved to backtest_trades.csv")
            
            # 打印最后5笔交易
            print("\nLast 5 Trades:")
            print(trades_df.tail().to_string(index=False))


# ============================================================================
# 数据获取
# ============================================================================

def get_russell1000_tickers():
    """
    获取 Russell 1000 成分股
    
    由于 Russell 1000 没有直接的 API，我们使用 Russell 2000 ETF (IWM)
    的主要持仓作为替代
    """
    # 这里我们使用一个简化的方法：获取热门的大盘股
    # 实际应用中可以从 Wikipedia 或其他数据源获取完整列表
    
    # Russell 1000 主要成分股示例（前 50 只）
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
        'V', 'JNJ', 'WMT', 'PG', 'XOM', 'CVX', 'LLY', 'ABBV', 'PFE',
        'MRK', 'KO', 'PEP', 'BAC', 'AVGO', 'COST', 'TMO', 'CRM',
        'ABT', 'MCD', 'CSCO', 'DHR', 'NKE', 'ACN', 'ADBE', 'NFLX',
        'LIN', 'WFC', 'TXN', 'ORCL', 'UNH', 'HD', 'CMCSA', 'DIS',
        'VZ', 'INTC', 'AMD', 'IBM', 'GE', 'HON', 'BA', 'CAT'
    ]
    
    logger.info(f"Using {len(tickers)} stocks for backtesting")
    return tickers


def download_data(tickers, start_date, end_date):
    """
    下载历史数据
    
    Args:
        tickers: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        dict: {ticker: DataFrame}
    """
    data = {}
    
    # 逐个下载以确保数据格式正确
    for i, ticker in enumerate(tickers):
        logger.info(f"Downloading {ticker} ({i+1}/{len(tickers)})")
        
        try:
            stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if stock_data.empty:
                logger.warning(f"  ✗ {ticker}: no data available")
                continue
            
            # 处理 MultiIndex 列名
            if isinstance(stock_data.columns, pd.MultiIndex):
                stock_data.columns = stock_data.columns.get_level_values(0)
            
            # 确保有足够的数据
            if len(stock_data) < 50:
                logger.warning(f"  ✗ {ticker}: insufficient data ({len(stock_data)} days)")
                continue
            
            # 确保索引是 datetime 类型
            stock_data.index = pd.to_datetime(stock_data.index)
            
            # 重命名列为小写（保持索引不变）
            stock_data.columns = [str(col).lower() for col in stock_data.columns]
            
            data[ticker] = stock_data
            logger.info(f"  ✓ {ticker}: {len(stock_data)} days")
            
        except Exception as e:
            logger.error(f"  ✗ {ticker}: error - {e}")
        
        # 添加延迟避免 API 限制
        time.sleep(0.5)
    
    logger.info(f"Successfully downloaded {len(data)}/{len(tickers)} stocks")
    return data


def download_vix(start_date, end_date):
    """
    下载 VIX 数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame: VIX 数据
    """
    try:
        vix_ticker = '^VIX'
        vix_data = yf.download(vix_ticker, start=start_date, end=end_date, progress=False)
        logger.info(f"Downloaded VIX data: {len(vix_data)} days")
        return vix_data
    except Exception as e:
        logger.error(f"Error downloading VIX: {e}")
        return None


# ============================================================================
# 主回测函数
# ============================================================================

def run_backtest(
    start_date='2021-01-01',
    end_date='2024-01-01',
    initial_cash=10000.0,
    plot_results=True
):
    """
    运行回测
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        initial_cash: 初始资金
        plot_results: 是否绘制结果
    """
    # 1. 获取股票列表
    logger.info("Getting Russell 1000 tickers...")
    tickers = get_russell1000_tickers()
    
    # 2. 下载数据
    logger.info(f"Downloading data from {start_date} to {end_date}...")
    data_dict = download_data(tickers, start_date, end_date)
    
    # 3. 下载 VIX
    logger.info("Downloading VIX data...")
    vix_data = download_vix(start_date, end_date)
    
    # 4. 创建 Cerebro 引擎
    cerebro = bt.Cerebro()
    
    # 5. 添加策略
    cerebro.addstrategy(SwingTradingStrategy)
    
    # 6. 添加数据
    for ticker, df in data_dict.items():
        # 数据已经准备好：日期是索引，列名是小写
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 使用索引作为日期
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        cerebro.adddata(data, name=ticker)
    
    # 7. 添加 VIX 数据（用于市场环境过滤）
    if vix_data is not None and not vix_data.empty:
        vix_feed = bt.feeds.PandasData(
            dataname=vix_data,
            datetime=None,
            open='Open',
            high='High',
            low='Low',
            close='Close',
            volume='Volume',
            openinterest=-1
        )
        cerebro.adddata(vix_feed, name='VIX')
        cerebro.addstrategy(SwingTradingStrategy, vix_data=vix_feed)
    
    # 8. 设置佣金（使用自定义佣金类）
    cerebro.broker.addcommissioninfo(IBKRCommission())
    
    # 9. 设置初始资金
    cerebro.broker.setcash(initial_cash)
    
    # 10. 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # 11. 运行回测
    logger.info("Running backtest...")
    print(f"\nStarting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
    
    results = cerebro.run()
    
    # 12. 打印分析器结果
    strat = results[0]
    
    print("\n" + "=" * 60)
    print("ANALYZER RESULTS")
    print("=" * 60)
    
    # Sharpe Ratio
    if hasattr(strat.analyzers.sharpe, 'get_analysis'):
        sharpe = strat.analyzers.sharpe.get_analysis()
        if 'sharperatio' in sharpe:
            print(f"Sharpe Ratio: {sharpe['sharperatio']:.2f}")
    
    # Drawdown
    if hasattr(strat.analyzers.drawdown, 'get_analysis'):
        dd = strat.analyzers.drawdown.get_analysis()
        print(f"Max Drawdown: {dd['max']['drawdown']:.2f}%")
        print(f"Max Drawdown Duration: {dd['max']['len']} days")
    
    # Trades
    if hasattr(strat.analyzers.trades, 'get_analysis'):
        trades = strat.analyzers.trades.get_analysis()
        if 'total' in trades:
            total = trades['total']
            print(f"\nTotal Trades: {total.get('total', 0)}")
            print(f"Winning Trades: {total.get('won', 0)}")
            print(f"Losing Trades: {total.get('lost', 0)}")
            
            if total.get('total', 0) > 0:
                win_rate = total.get('won', 0) / total['total'] * 100
                print(f"Win Rate: {win_rate:.2f}%")
    
    # 13. 绘制结果
    if plot_results:
        logger.info("Plotting results...")
        cerebro.plot(style='candlestick', barup='green', bardown='red')
        plt.show()
    
    return cerebro


# ============================================================================
# 主程序
# ============================================================================

if __name__ == '__main__':
    # 设置日期范围（3年）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
    
    logger.info(f"Backtesting from {start_date} to {end_date}")
    
    # 运行回测
    cerebro = run_backtest(
        start_date=start_date,
        end_date=end_date,
        initial_cash=10000.0,
        plot_results=True
    )