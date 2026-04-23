"""
回测测试脚本
测试 3 年数据，50 只 Russell 1000 随机股票
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtest_engine import run_backtest, get_russell1000_tickers, download_data
from datetime import datetime, timedelta
import logging
import random

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_russell1000_expanded():
    """
    获取扩展的 Russell 1000 股票列表（前 100 只）
    """
    # Russell 1000 主要成分股（按行业分类）
    tickers = [
        # Technology
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ADBE',
        'CSCO', 'CRM', 'NFLX', 'INTC', 'AMD', 'TXN', 'AVGO', 'QCOM', 'ORCL', 'IBM',
        'ACN', 'NOW', 'ADP', 'INTU', 'SAP', 'PLTR', 'SNOW', 'ZM', 'DOCU', 'TWLO',
        
        # Financials
        'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'USB', 'PNC',
        'TFC', 'COF', 'AXP', 'CB', 'MMC', 'AON', 'AIG', 'MET', 'PRU', 'LNC',
        'SPGI', 'MCO', 'ICE', 'CME', 'DFS', 'SYF', 'ALLY', 'KEY', 'RF', 'HBAN',
        
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY',
        'AMGN', 'GILD', 'CVS', 'MDT', 'ISRG', 'REGN', 'VRTX', 'BIIB', 'MRNA', 'EL',
        'BSX', 'RMD', 'HCA', 'CI', 'ANTM', 'HUM', 'CNC', 'DGX', 'IQV', 'ILMN',
        
        # Consumer Discretionary
        'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG', 'MAR',
        'CMG', 'DHI', 'NVR', 'LVS', 'MGM', 'CCL', 'RCL', 'TSLA', 'EBAY', 'ETSY',
        'ROST', 'FIVE', 'AZO', 'ORLY', 'GPC', 'APTV', 'AAP', 'CROX', 'LULU', 'ON',
        
        # Communication Services
        'GOOGL', 'GOOG', 'META', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR',
        'EA', 'TTWO', 'ATVI', 'FOX', 'FOXA', 'PARA', 'DISCA', 'DISCK', 'NTES', 'BIDU',
        
        # Industrials
        'HON', 'CAT', 'UPS', 'BA', 'GE', 'RTX', 'LMT', 'UNP', 'DE', 'MMM',
        'EMR', 'ITW', 'ETN', 'CMI', 'GD', 'NOC', 'PH', 'CAT', 'ROP', 'JCI',
        'PCAR', 'FDX', 'URI', 'DOV', 'OTIS', 'CARR', 'WM', 'RSG', 'CPRT', 'CTAS',
        
        # Consumer Staples
        'PG', 'KO', 'PEP', 'WMT', 'COST', 'PM', 'MO', 'MDLZ', 'CL', 'KMB',
        'CLX', 'HSY', 'K', 'SYY', 'CAG', 'MKC', 'GIS', 'STZ', 'BTI', 'ADM',
        
        # Energy
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'PXD',
        'FANG', 'HAL', 'BKR', 'WMB', 'ET', 'KMI', 'OKE', 'HES', 'DVN', 'APA',
        
        # Utilities
        'NEE', 'DUK', 'SO', 'D', 'EXC', 'AEP', 'SRE', 'XEL', 'ED', 'PEG',
        'EIX', 'PPL', 'ES', 'ETR', 'AWK', 'WEC', 'FE', 'DTE', 'CNP', 'CMS',
        
        # Real Estate
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'O', 'DLR', 'VICI', 'SPG', 'CBRE',
        'PRO', 'AVB', 'EQR', 'ESS', 'VTR', 'WELL', 'BXP', 'HCP', 'VNO', 'SLG',
    ]
    
    # 去重
    tickers = list(set(tickers))
    
    logger.info(f"Using {len(tickers)} Russell 1000 stocks for backtesting")
    return tickers


def test_expanded_backtest():
    """
    扩展回测测试
    - 时间范围：3 年（2023-01-01 到现在）
    - 股票数量：50 只随机 Russell 1000 股票
    """
    print("=" * 60)
    print("EXPANDED BACKTEST TEST")
    print("=" * 60)
    
    # 设置日期范围（3年）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
    
    print(f"\nTest Configuration:")
    print(f"  Date Range: {start_date} to {end_date} (3 years)")
    print(f"  Stock Pool: Russell 1000")
    print(f"  Stocks to Test: 50 (randomly selected)")
    print(f"  Initial Capital: $10,000")
    
    # 获取股票池
    print(f"\nBuilding stock pool...")
    all_tickers = get_russell1000_expanded()
    
    # 随机选择 50 只股票
    random.seed(42)  # 固定种子以便复现
    selected_tickers = random.sample(all_tickers, min(50, len(all_tickers)))
    
    print(f"  Total pool: {len(all_tickers)} stocks")
    print(f"  Selected: {len(selected_tickers)} stocks")
    print(f"  Sample tickers: {', '.join(selected_tickers[:10])}...")
    
    try:
        # 下载测试数据
        print(f"\nDownloading data for {len(selected_tickers)} stocks...")
        print("  This may take a few minutes...")
        data_dict = download_data(selected_tickers, start_date, end_date)
        
        if not data_dict:
            print("❌ No data downloaded!")
            return False
        
        print(f"✓ Downloaded {len(data_dict)} stocks")
        
        # 下载 VIX 数据
        print("\nDownloading VIX data...")
        vix_data = download_vix(start_date, end_date)
        
        if vix_data is not None and not vix_data.empty:
            print(f"✓ Downloaded VIX data: {len(vix_data)} days")
        else:
            print("⚠ Warning: VIX data not available, proceeding without market filter")
        
        # 下载 SPY 数据
        print("\nDownloading SPY data...")
        spy_data = download_spy(start_date, end_date)
        
        if spy_data is not None and not spy_data.empty:
            print(f"✓ Downloaded SPY data: {len(spy_data)} days")
        else:
            print("⚠ Warning: SPY data not available, proceeding without market regime filter")
        
        # 创建 Cerebro
        import backtrader as bt
        cerebro = bt.Cerebro()
        
        # 添加策略
        from src.backtest_engine import SwingTradingStrategy
        cerebro.addstrategy(SwingTradingStrategy)
        
        # 添加股票数据
        for ticker, df in data_dict.items():
            data = bt.feeds.PandasData(
                dataname=df,
                datetime=None,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=-1
            )
            cerebro.adddata(data, name=ticker)
        
        # 添加 VIX 数据（如果有）
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
        
        # 添加 SPY 数据（如果有）
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
        
        # 设置佣金
        from src.backtest_engine import IBKRCommission
        cerebro.broker.addcommissioninfo(IBKRCommission())
        
        # 设置初始资金
        cerebro.broker.setcash(10000.0)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 运行回测
        print(f"\nStarting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
        print("\nRunning backtest...")
        results = cerebro.run()
        
        strat = results[0]
        
        print(f"\nFinal Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
        print(f"Total Return: {(cerebro.broker.getvalue() - 10000) / 10000 * 100:+.2f}%")
        print(f"Total Trades: {strat.trade_count}")
        print(f"Winning Trades: {strat.winning_trades}")
        print(f"Losing Trades: {strat.losing_trades}")
        
        if strat.trade_count > 0:
            win_rate = strat.winning_trades / strat.trade_count * 100
            print(f"Win Rate: {win_rate:.2f}%")
        
        print(f"Maximum Drawdown: {strat.max_drawdown * 100:.2f}%")
        
        # 打印分析器结果
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
        
        print("\n" + "=" * 60)
        print("✅ EXPANDED BACKTEST COMPLETED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def download_vix(start_date, end_date):
    """下载 VIX 数据"""
    try:
        import yfinance as yf
        vix_data = yf.download('^VIX', start=start_date, end=end_date, progress=False)
        
        if vix_data.empty:
            return None
        
        if isinstance(vix_data.columns, pd.MultiIndex):
            vix_data.columns = vix_data.columns.get_level_values(0)
        
        vix_data.index = pd.to_datetime(vix_data.index)
        vix_data.columns = [str(col).lower() for col in vix_data.columns]
        
        return vix_data
    except Exception as e:
        logger.error(f"Error downloading VIX: {e}")
        return None


def download_spy(start_date, end_date):
    """下载 SPY 数据"""
    try:
        import yfinance as yf
        spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False)
        
        if spy_data.empty:
            return None
        
        if isinstance(spy_data.columns, pd.MultiIndex):
            spy_data.columns = spy_data.columns.get_level_values(0)
        
        spy_data.index = pd.to_datetime(spy_data.index)
        spy_data.columns = [str(col).lower() for col in spy_data.columns]
        
        return spy_data
    except Exception as e:
        logger.error(f"Error downloading SPY: {e}")
        return None


if __name__ == '__main__':
    import pandas as pd  # 需要导入 pandas
    success = test_expanded_backtest()
    sys.exit(0 if success else 1)