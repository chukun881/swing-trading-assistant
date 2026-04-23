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
# 交易策略 - 纯突破 + 移动止损 + 市场环境过滤
# ============================================================================

class SwingTradingStrategy(bt.Strategy):
    """
    纯突破动量策略
    
    入场：Close > BB Upper AND 60 < RSI < 80
    
    市场过滤：
    - SPY Close > SMA200（牛市确认）
    - VIX < 30（低风险环境）
    
    退出：
    - 硬止损：Close < Entry_Price * 0.95
    - 移动止损：Close < EMA20
    """
    params = (
        ('position_size', 0.10),  # 每次交易使用 10% 资金
        ('vix_threshold', 30.0),  # VIX 阈值
    )
    
    def __init__(self):
        # 为每个数据源计算指标
        self.indicators = {}
        
        for data in self.datas:
            if data._name in ['VIX', 'SPY']:
                continue
            
            # 计算指标
            self.indicators[data._name] = {
                'ema20': bt.indicators.EMA(data, period=20),
                'ema50': bt.indicators.EMA(data, period=50),
                'rsi': bt.indicators.RSI(data, period=14),
                'bb': bt.indicators.BollingerBands(data, period=20, devfactor=2.0),
            }
        
        # 获取市场数据（安全处理，因为 VIX 和 SPY 可能不存在）
        self.vix = None
        self.spy = None
        self.spy_sma200 = None
        
        try:
            self.vix = self.getdatabyname('VIX')
        except KeyError:
            logger.warning("VIX data not available, VIX filter disabled")
        
        try:
            self.spy = self.getdatabyname('SPY')
            # 计算 SPY 的 200日 SMA
            self.spy_sma200 = bt.indicators.SMA(self.spy, period=200)
        except KeyError:
            logger.warning("SPY data not available, market regime filter disabled")
        
        # 交易记录
        self.trades = []
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # 记录最大回撤
        self.max_equity = self.broker.getvalue()
        self.max_drawdown = 0.0
        
        # 跟踪当前持仓
        self.entry_prices = {}
        self.entry_dates = {}
        
    def next(self):
        """每个 bar 调用"""
        # 更新最大回撤
        current_equity = self.broker.getvalue()
        if current_equity > self.max_equity:
            self.max_equity = current_equity
        drawdown = (self.max_equity - current_equity) / self.max_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # 检查市场过滤器
        # 1. VIX 过滤器（如果 VIX 数据可用）
        if self.vix is not None and self.vix.close[0] > self.p.vix_threshold:
            # VIX > 30，不产生新买入信号
            return
        
        # 2. SPY 市场环境过滤器（如果 SPY 数据可用）
        if self.spy is not None and self.spy_sma200 is not None:
            if self.spy.close[0] < self.spy_sma200[0]:
                # SPY 在 200日均线之下，熊市，不产生新买入信号
                return
        
        # 收集所有买入信号
        buy_signals = []
        
        for data in self.datas:
            if data._name in ['VIX', 'SPY']:
                continue
            
            # 如果已持有该股票，检查退出信号
            if self.getposition(data).size > 0:
                self.check_exit_signals(data)
                continue
            
            # 检测买入信号
            signal = self.check_entry_signals(data)
            if signal:
                buy_signals.append(signal)
        
        # 如果有多个信号，按优先级排序
        if buy_signals:
            # 排序逻辑：按 RSI 从高到低排序（最强优先）
            buy_signals.sort(key=lambda x: x['rsi'], reverse=True)
            
            # 按顺序执行买入
            for signal in buy_signals:
                data = signal['data']
                
                # 检查是否有足够现金
                required_cash = self.broker.getvalue() * self.p.position_size
                if self.broker.getcash() < required_cash:
                    # 资金不足，跳过
                    continue
                
                # 执行买入
                self.enter_position(signal)
    
    def check_entry_signals(self, data):
        """
        检查入场信号 - 纯突破策略
        
        Breakout: Close > BB Upper AND 60 < RSI < 80
        """
        symbol = data._name
        ind = self.indicators[symbol]
        
        close = data.close[0]
        rsi = ind['rsi'][0]
        bb_upper = ind['bb'].top[0]
        
        # Breakout 信号：Close > BB Upper AND 60 < RSI < 80
        if close > bb_upper and 60 < rsi < 80:
            return {
                'data': data,
                'symbol': symbol,
                'price': close,
                'rsi': rsi,
            }
        
        return None
    
    def enter_position(self, signal):
        """入场"""
        data = signal['data']
        symbol = signal['symbol']
        
        # 使用 PercentSizer 自动计算仓位大小
        self.buy(data=data)
        
        self.entry_prices[symbol] = signal['price']
        self.entry_dates[symbol] = data.datetime.date(0)
        
        logger.info(f"ENTER BREAKOUT: {symbol} at ${signal['price']:.2f}, RSI={signal['rsi']:.1f}")
    
    def check_exit_signals(self, data):
        """
        检查退出信号
        
        1. 硬止损：Close < Entry_Price * 0.95
        2. 移动止损：Close < EMA20
        """
        symbol = data._name
        ind = self.indicators[symbol]
        
        close = data.close[0]
        ema20 = ind['ema20'][0]
        entry_price = self.entry_prices.get(symbol, close)
        
        # 退出条件
        exit_reason = None
        
        # 1. 硬止损 -5%
        if close < entry_price * 0.95:
            exit_reason = "Stop Loss (-5%)"
        
        # 2. 移动止损：价格跌破 EMA20
        elif close < ema20:
            exit_reason = "Trailing Stop (EMA20)"
        
        if exit_reason:
            self.close_position(data, exit_reason)
    
    def close_position(self, data, reason):
        """平仓"""
        symbol = data._name
        current_price = data.close[0]
        entry_price = self.entry_prices.get(symbol, current_price)
        entry_date = self.entry_dates.get(symbol, data.datetime.date(0))
        
        # 记录交易
        pnl = (current_price - entry_price) / entry_price
        
        trade_info = {
            'symbol': symbol,
            'entry_date': entry_date,
            'exit_date': data.datetime.date(0),
            'entry_price': entry_price,
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
        
        logger.info(f"EXIT {symbol} at ${current_price:.2f}, PnL={pnl*100:+.2f}%, Reason={reason}")
        
        # 平仓
        self.close(data=data)
        
        # 清除记录
        del self.entry_prices[symbol]
        del self.entry_dates[symbol]
    
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
    """
    # Russell 1000 主要成分股（前 100 只）
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
        'V', 'JNJ', 'WMT', 'PG', 'XOM', 'CVX', 'LLY', 'ABBV', 'PFE', 'MRK',
        'KO', 'PEP', 'BAC', 'AVGO', 'COST', 'TMO', 'CRM', 'ABT', 'MCD', 'CSCO',
        'DHR', 'NKE', 'ACN', 'ADBE', 'NFLX', 'LIN', 'WFC', 'TXN', 'ORCL', 'UNH',
        'HD', 'CMCSA', 'VZ', 'DIS', 'INTC', 'AMD', 'IBM', 'GE', 'HON', 'BA',
        'CAT', 'UPS', 'RTX', 'LMT', 'UNP', 'DE', 'MMM', 'EMR', 'ITW', 'ETN',
        'CMI', 'GD', 'NOC', 'PH', 'PCAR', 'FDX', 'URI', 'DOV', 'OTIS', 'CARR',
        'WM', 'RSG', 'CPRT', 'CTAS', 'EBAY', 'PYPL', 'ADP', 'INTU', 'NOW', 'FIS',
        'ISRG', 'REGN', 'VRTX', 'BIIB', 'MRNA', 'EL', 'BSX', 'RMD', 'HCA', 'CI',
        'ANTM', 'HUM', 'CNC', 'DGX', 'IQV', 'ILMN', 'DLR', 'VICI', 'SPG', 'CBRE',
    ]
    
    logger.info(f"Using {len(tickers)} Russell 1000 stocks for backtesting")
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
        
        if vix_data.empty:
            logger.warning("No VIX data available")
            return None
        
        # 处理 MultiIndex 列名（如果有）
        if isinstance(vix_data.columns, pd.MultiIndex):
            vix_data.columns = vix_data.columns.get_level_values(0)
        
        # 确保索引是 datetime 类型
        vix_data.index = pd.to_datetime(vix_data.index)
        
        # 重命名列为小写
        vix_data.columns = [str(col).lower() for col in vix_data.columns]
        
        logger.info(f"Downloaded VIX data: {len(vix_data)} days")
        return vix_data
    except Exception as e:
        logger.error(f"Error downloading VIX: {e}")
        return None


def download_spy(start_date, end_date):
    """
    下载 SPY 数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame: SPY 数据
    """
    try:
        spy_ticker = 'SPY'
        spy_data = yf.download(spy_ticker, start=start_date, end=end_date, progress=False)
        
        if spy_data.empty:
            logger.warning("No SPY data available")
            return None
        
        # 处理 MultiIndex 列名（如果有）
        if isinstance(spy_data.columns, pd.MultiIndex):
            spy_data.columns = spy_data.columns.get_level_values(0)
        
        # 确保索引是 datetime 类型
        spy_data.index = pd.to_datetime(spy_data.index)
        
        # 重命名列为小写
        spy_data.columns = [str(col).lower() for col in spy_data.columns]
        
        logger.info(f"Downloaded SPY data: {len(spy_data)} days")
        return spy_data
    except Exception as e:
        logger.error(f"Error downloading SPY: {e}")
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
    
    # 4. 下载 SPY
    logger.info("Downloading SPY data...")
    spy_data = download_spy(start_date, end_date)
    
    # 5. 创建 Cerebro 引擎
    cerebro = bt.Cerebro()
    
    # 6. 添加策略
    cerebro.addstrategy(SwingTradingStrategy)
    
    # 7. 添加股票数据
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
    
    # 8. 添加 VIX 数据
    if vix_data is not None and not vix_data.empty:
        vix_feed = bt.feeds.PandasData(
            dataname=vix_data,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        cerebro.adddata(vix_feed, name='VIX')
        logger.info("VIX data feed added to cerebro")
    else:
        logger.warning("No VIX data available, proceeding without market filter")
    
    # 9. 添加 SPY 数据
    if spy_data is not None and not spy_data.empty:
        spy_feed = bt.feeds.PandasData(
            dataname=spy_data,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        cerebro.adddata(spy_feed, name='SPY')
        logger.info("SPY data feed added to cerebro")
    else:
        logger.warning("No SPY data available, proceeding without market regime filter")
    
    # 10. 设置仓位大小（10% of portfolio）
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    
    # 11. 设置佣金（使用自定义佣金类）
    cerebro.broker.addcommissioninfo(IBKRCommission())
    
    # 12. 设置初始资金
    cerebro.broker.setcash(initial_cash)
    
    # 13. 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # 14. 运行回测
    logger.info("Running backtest...")
    print(f"\nStarting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
    
    results = cerebro.run()
    
    # 15. 打印分析器结果
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
    
    # 16. 绘制结果
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