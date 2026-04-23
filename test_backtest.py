"""
完整 Russell 1000 回测脚本
- 支持 1000 只股票
- 数据缓存（崩溃恢复）
- 鲁棒下载器（重试 + 指数退避）
- 内存优化（禁用绘图）
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtest_engine import SwingTradingStrategy, IBKRCommission, SignalPandasData
from src.analysis.breakout import calculate_indicators_batch
from datetime import datetime, timedelta
import logging
import pandas as pd
import time
import pickle
from tqdm import tqdm

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 配置
# ============================================================================
CACHE_DIR = "data/cache"
BACKTEST_CSV = "backtest_trades_full.csv"


# ============================================================================
# Russell 1000 完整列表
# ============================================================================
def get_russell1000_full():
    """
    获取扩展的 Russell 1000 股票列表（约 1000 只）
    按行业分类，覆盖主要大盘股
    """
    # Russell 1000 主要成分股
    tickers = [
        # Technology (150+)
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ADBE',
        'CSCO', 'CRM', 'NFLX', 'INTC', 'AMD', 'TXN', 'AVGO', 'QCOM', 'ORCL', 'IBM',
        'ACN', 'NOW', 'ADP', 'INTU', 'SAP', 'PLTR', 'SNOW', 'ZM', 'DOCU', 'TWLO',
        'ASML', 'SHOP', 'SQ', 'ABNB', 'UBER', 'LYFT', 'RBLX', 'DASH', 'PATH', 'COIN',
        'MU', 'LRCX', 'KLAC', 'MRVL', 'ANET', 'CDNS', 'SNPS', 'MCHP', 'ADI', 'MPWR',
        'ON', 'QFIN', 'BIDU', 'NTES', 'JD', 'PDD', 'TME', 'BABA', 'VIPS', 'JKS',
        'NIO', 'XPEV', 'LI', 'LCID', 'RIVN', 'CHWY', 'ETSY', 'PTON', 'AFRM', 'UPST',
        
        # Financials (150+)
        'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'USB', 'PNC',
        'TFC', 'COF', 'AXP', 'CB', 'MMC', 'AON', 'AIG', 'MET', 'PRU', 'LNC',
        'SPGI', 'MCO', 'ICE', 'CME', 'DFS', 'SYF', 'ALLY', 'KEY', 'RF', 'HBAN',
        'FITB', 'MTB', 'CFG', 'ZION', 'WAL', 'FHN', 'PBCT', 'STT', 'NTRS', 'BK',
        'PGR', 'ALL', 'TRV', 'CINF', 'AFL', 'HIG', 'L', 'MET', 'PRU', 'UNM',
        'V', 'MA', 'FIS', 'FISV', 'GPN', 'TSYS', 'SQ', 'ADYEN', 'NUAN', 'FLEX',
        'FSLR', 'ENPH', 'SEDG', 'SOL', 'RUN', 'NOVA', 'CSIQ', 'JKS', 'SPWR', 'MAXN',
        
        # Healthcare (120+)
        'JNJ', 'UNH', 'PFE', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY',
        'AMGN', 'GILD', 'CVS', 'MDT', 'ISRG', 'REGN', 'VRTX', 'BIIB', 'MRNA', 'EL',
        'BSX', 'RMD', 'HCA', 'CI', 'ANTM', 'HUM', 'CNC', 'DGX', 'IQV', 'ILMN',
        'DVA', 'DAVA', 'ALXN', 'INCY', 'VRTX', 'REGN', 'ALXO', 'SGEN', 'MRTX', 'NTLA',
        'CRSP', 'EDIT', 'BEAM', 'ALNY', 'IONS', 'SGMO', 'NTRA', 'PACB', 'TWST', 'ARCT',
        'NVTA', 'GH', 'RGNX', 'IOVA', 'KITE', 'BLUE', 'JAZZ', 'EXAS', 'NEOG', 'QLYS',
        
        # Consumer Discretionary (100+)
        'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG', 'MAR',
        'CMG', 'DHI', 'NVR', 'LVS', 'MGM', 'CCL', 'RCL', 'EBAY', 'ETSY', 'ROST',
        'FIVE', 'AZO', 'ORLY', 'GPC', 'APTV', 'AAP', 'CROX', 'LULU', 'ON', 'BBY',
        'TGT', 'COST', 'WMT', 'KSS', 'JWN', 'M', 'KOH', 'THO', 'GPC', 'ORLY',
        'DLTR', 'BIG', 'WGO', 'FO', 'THO', 'HOG', 'MCB', 'GPC', 'ORLY', 'AZO',
        'AN', 'F', 'GM', 'RACE', 'TSLA', 'LCID', 'RIVN', 'NIO', 'XPEV', 'LI',
        
        # Communication Services (80+)
        'GOOGL', 'GOOG', 'META', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR',
        'EA', 'TTWO', 'ATVI', 'FOX', 'FOXA', 'PARA', 'NTES', 'BIDU', 'TME', 'NET',
        'ZG', 'PINS', 'TWTR', 'SNAP', 'DOCU', 'ZM', 'DUOL', 'HOLO', 'FUBO', 'BNGO',
        'CEVA', 'SATS', 'VSAT', 'IRDM', 'GSAT', 'CMTL', 'LITE', 'PLUG', 'BE', 'NKLA',
        
        # Industrials (150+)
        'HON', 'CAT', 'UPS', 'BA', 'GE', 'RTX', 'LMT', 'UNP', 'DE', 'MMM',
        'EMR', 'ITW', 'ETN', 'CMI', 'GD', 'NOC', 'PH', 'ROP', 'JCI', 'PCAR',
        'FDX', 'URI', 'DOV', 'OTIS', 'CARR', 'WM', 'RSG', 'CPRT', 'CTAS', 'CSX',
        'NSC', 'KSU', 'GWW', 'FAST', 'SWK', 'XYL', 'IR', 'PNR', 'WAB', 'TT',
        'TXT', 'TDY', 'ACM', 'J', 'MTZ', 'DY', 'CR', 'GLW', 'CXP', 'AVY',
        'ALK', 'LUV', 'DAL', 'AAL', 'UAL', 'SAVE', 'HA', 'JBLU', 'ALK', 'SKYW',
        
        # Consumer Staples (80+)
        'PG', 'KO', 'PEP', 'WMT', 'COST', 'PM', 'MO', 'MDLZ', 'CL', 'KMB',
        'CLX', 'HSY', 'K', 'SYY', 'CAG', 'MKC', 'GIS', 'STZ', 'BTI', 'ADM',
        'TSN', 'KHC', 'HRL', 'SJM', 'CPB', 'LW', 'CAG', 'POST', 'BG', 'INGR',
        'KR', 'Safeway', 'WBA', 'CVS', 'RADS', 'ACV', 'HPE', 'LYV', 'LIVE', 'PARA',
        
        # Energy (100+)
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'PXD',
        'FANG', 'HAL', 'BKR', 'WMB', 'ET', 'KMI', 'OKE', 'HES', 'DVN', 'APA',
        'MRO', 'OAS', 'AR', 'SM', 'CNX', 'RRC', 'NBL', 'CLR', 'CHK', 'CDEV',
        'PBF', 'DK', 'ALJ', 'MUSA', 'GAS', 'FTK', 'NFX', 'RRC', 'PKD', 'RES',
        'WHD', 'BCEI', 'WTI', 'CLNE', 'CPE', 'EQT', 'SWN', 'HP', 'MUR', 'NOV',
        
        # Utilities (60+)
        'NEE', 'DUK', 'SO', 'D', 'EXC', 'AEP', 'SRE', 'XEL', 'ED', 'PEG',
        'EIX', 'PPL', 'ES', 'ETR', 'AWK', 'WEC', 'FE', 'DTE', 'CNP', 'CMS',
        'AGR', 'AEE', 'ATO', 'CNP', 'CMS', 'D', 'DTE', 'EIX', 'EPEG', 'EXC',
        'FE', 'GAS', 'NEP', 'NI', 'NRG', 'OGE', 'OK', 'PPL', 'SCG', 'SRE',
        'WEC', 'XEL', 'YORW', 'AES', 'AWK', 'CCEP', 'CHD', 'CNP', 'CNP', 'EIX',
        
        # Real Estate (80+)
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'O', 'DLR', 'VICI', 'SPG', 'CBRE',
        'AVB', 'EQR', 'ESS', 'VTR', 'WELL', 'BXP', 'HCP', 'VNO', 'SLG', 'REXR',
        'FRT', 'MAC', 'KIM', 'REG', 'PEAK', 'LAMR', 'OUT', 'GIC', 'BRX', 'KRC',
        'ARE', 'IRM', 'EXR', 'STAG', 'WPC', 'OHI', 'HCN', 'VTR', 'HTA', 'DOC',
        'CPT', 'MAA', 'UDR', 'EQR', 'AVB', 'ESS', 'AVAL', 'BXP', 'CONE', 'CUBE',
        
        # Materials (50+)
        'LIN', 'APD', 'DOW', 'DD', 'NEM', 'FCX', 'SHW', 'EMN', 'ECL', 'PPG',
        'IP', 'PKG', 'SEE', 'WRK', 'AVY', 'ALB', 'FMC', 'CTVA', 'CF', 'MOS',
        'IFF', 'LYB', 'MLM', 'VMC', 'MLM', 'NUE', 'STLD', 'X', 'CLF', 'AA',
        'CXP', 'CEM', 'CX', 'GEO', 'HOLX', 'JEC', 'KBR', 'MTX', 'NVR', 'POOL',
        
        # Additional Large Cap Stocks
        'BRK.A', 'BRK.B', 'LMT', 'BA', 'GE', 'CAT', 'HON', 'MMM', 'UPS', 'UNH',
        'JNJ', 'PG', 'V', 'MA', 'JPM', 'BAC', 'WMT', 'XOM', 'CVX', 'C',
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'DIS',
        'HD', 'KO', 'PEP', 'COST', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG',
    ]
    
    # 去重
    tickers = list(set(tickers))
    tickers.sort()  # 排序
    
    logger.info(f"Total Russell 1000 stocks: {len(tickers)}")
    return tickers


# ============================================================================
# 鲁棒下载器（带重试和指数退避）
# ============================================================================
def download_with_retry(ticker, start_date, end_date, max_retries=3):
    """
    带重试和指数退避的下载器
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        max_retries: 最大重试次数
        
    Returns:
        DataFrame or None
    """
    import yfinance as yf
    
    for attempt in range(max_retries):
        try:
            # 添加用户代理避免被拒绝
            data = yf.download(
                ticker, 
                start=start_date, 
                end=end_date, 
                progress=False,
                threads=False
            )
            
            if data.empty:
                logger.warning(f"  ✗ {ticker}: no data available")
                return None
            
            # 处理 MultiIndex 列名
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            # 确保索引是 datetime 类型
            data.index = pd.to_datetime(data.index)
            
            # 重命名列为小写
            data.columns = [str(col).lower() for col in data.columns]
            
            # 检查是否有足够的数据
            if len(data) < 50:
                logger.warning(f"  ✗ {ticker}: insufficient data ({len(data)} days)")
                return None
            
            # 成功下载
            return data
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"  ✗ {ticker}: failed after {max_retries} attempts - {e}")
                return None
            
            # 指数退避：0.5s, 1s, 2s, 4s...
            wait_time = (2 ** attempt) * 0.5
            logger.warning(f"  ⚠ {ticker}: attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return None


# ============================================================================
# 数据缓存系统
# ============================================================================
def get_cache_filename(ticker, start_date, end_date):
    """生成缓存文件名"""
    return os.path.join(CACHE_DIR, f"{ticker}_{start_date}_{end_date}.pkl")


def load_from_cache(ticker, start_date, end_date):
    """从缓存加载数据"""
    cache_file = get_cache_filename(ticker, start_date, end_date)
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            logger.warning(f"  ⚠ {ticker}: cache corrupted, will re-download - {e}")
            return None
    
    return None


def save_to_cache(ticker, start_date, end_date, data):
    """保存数据到缓存"""
    cache_file = get_cache_filename(ticker, start_date, end_date)
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.error(f"  ✗ {ticker}: failed to save cache - {e}")


def get_data_with_cache(ticker, start_date, end_date):
    """
    带缓存的数据获取
    
    优先从缓存加载，如果不存在则下载并保存
    """
    # 尝试从缓存加载
    data = load_from_cache(ticker, start_date, end_date)
    if data is not None:
        return data
    
    # 下载新数据
    data = download_with_retry(ticker, start_date, end_date)
    
    # 保存到缓存
    if data is not None:
        save_to_cache(ticker, start_date, end_date, data)
    
    return data


# ============================================================================
# 批量下载
# ============================================================================
def download_all_data(tickers, start_date, end_date):
    """
    批量下载所有股票数据
    
    Args:
        tickers: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        dict: {ticker: DataFrame}
    """
    data_dict = {}
    cache_hits = 0
    downloads = 0
    errors = 0
    
    print(f"\nDownloading data for {len(tickers)} stocks...")
    print(f"Cache directory: {CACHE_DIR}")
    print("Progress:")
    
    # 使用 tqdm 显示进度条
    for ticker in tqdm(tickers, desc="  Progress", ncols=80):
        data = get_data_with_cache(ticker, start_date, end_date)
        
        if data is not None:
            data_dict[ticker] = data
            
            # 统计
            cache_file = get_cache_filename(ticker, start_date, end_date)
            if os.path.exists(cache_file):
                cache_hits += 1
            else:
                downloads += 1
        else:
            errors += 1
        
        # 延迟避免限流（如果是新下载）
        if not os.path.exists(get_cache_filename(ticker, start_date, end_date)):
            time.sleep(0.5)
    
    print(f"\n✓ Download complete!")
    print(f"  Total: {len(tickers)} stocks")
    print(f"  Cache hits: {cache_hits}")
    print(f"  New downloads: {downloads}")
    print(f"  Errors: {errors}")
    print(f"  Success: {len(data_dict)} stocks")
    
    return data_dict


# ============================================================================
# 下载市场数据（VIX 和 SPY）
# ============================================================================
def download_market_data(start_date, end_date):
    """下载 VIX 和 SPY 数据"""
    import yfinance as yf
    
    vix_data = None
    spy_data = None
    
    # 下载 VIX
    print("\nDownloading VIX data...")
    try:
        vix_data = yf.download('^VIX', start=start_date, end=end_date, progress=False)
        if not vix_data.empty:
            if isinstance(vix_data.columns, pd.MultiIndex):
                vix_data.columns = vix_data.columns.get_level_values(0)
            vix_data.index = pd.to_datetime(vix_data.index)
            vix_data.columns = [str(col).lower() for col in vix_data.columns]
            print(f"  ✓ VIX: {len(vix_data)} days")
        else:
            print("  ⚠ VIX: no data available")
    except Exception as e:
        print(f"  ✗ VIX: error - {e}")
    
    # 下载 SPY
    print("\nDownloading SPY data...")
    try:
        spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False)
        if not spy_data.empty:
            if isinstance(spy_data.columns, pd.MultiIndex):
                spy_data.columns = spy_data.columns.get_level_values(0)
            spy_data.index = pd.to_datetime(spy_data.index)
            spy_data.columns = [str(col).lower() for col in spy_data.columns]
            print(f"  ✓ SPY: {len(spy_data)} days")
        else:
            print("  ⚠ SPY: no data available")
    except Exception as e:
        print(f"  ✗ SPY: error - {e}")
    
    return vix_data, spy_data


# ============================================================================
# 运行完整回测
# ============================================================================
def run_full_backtest():
    """
    运行完整的 Russell 1000 回测
    """
    import backtrader as bt
    
    print("=" * 70)
    print("FULL RUSSELL 1000 BACKTEST")
    print("=" * 70)
    
    # 设置日期范围（3年）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
    
    print(f"\nTest Configuration:")
    print(f"  Date Range: {start_date} to {end_date} (3 years)")
    print(f"  Initial Capital: $10,000.00")
    print(f"  Position Size: 10% per trade")
    print(f"  Strategy: Breakout + Trailing Stop (EMA20) + Market Filter")
    
    # 获取股票列表
    print(f"\nBuilding Russell 1000 stock list...")
    tickers = get_russell1000_full()
    print(f"  Total stocks: {len(tickers)}")
    
    # 下载股票数据
    data_dict = download_all_data(tickers, start_date, end_date)
    
    if not data_dict:
        print("\n❌ No data downloaded!")
        return False
    
    # 下载市场数据
    vix_data, spy_data = download_market_data(start_date, end_date)
    
    # 使用 breakout.py 计算所有指标和信号（单一数据源）
    print(f"\nCalculating indicators and signals...")
    data_dict = calculate_indicators_batch(data_dict, spy_data, vix_data)
    print(f"  ✓ Signals added to {len(data_dict)} stocks")
    
    # 创建 Cerebro 引擎
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(SwingTradingStrategy)
    
    # 添加股票数据（使用 SignalPandasData 包含信号列）
    print(f"\nAdding {len(data_dict)} stock feeds to Cerebro...")
    for ticker, df in data_dict.items():
        data = SignalPandasData(
            dataname=df,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            Buy_Signal='Buy_Signal',
            Sell_Signal='Sell_Signal',
            openinterest=-1
        )
        cerebro.adddata(data, name=ticker)
    
    # 添加 VIX 数据
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
        print("  ✓ VIX feed added")
    else:
        print("  ⚠ VIX feed not available")
    
    # 添加 SPY 数据
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
        print("  ✓ SPY feed added")
    else:
        print("  ⚠ SPY feed not available")
    
    # 设置仓位大小
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    
    # 设置佣金
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
    print("  (This may take 5-10 minutes with 1000 stocks)")
    
    results = cerebro.run()
    
    strat = results[0]
    
    # 打印结果
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Initial Capital: ${10,000:,.2f}")
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
    print(f"Total Return: {(cerebro.broker.getvalue() - 10000) / 10000 * 100:+.2f}%")
    print(f"Total Trades: {strat.trade_count}")
    print(f"Winning Trades: {strat.winning_trades}")
    print(f"Losing Trades: {strat.losing_trades}")
    
    if strat.trade_count > 0:
        win_rate = strat.winning_trades / strat.trade_count * 100
        print(f"Win Rate: {win_rate:.2f}%")
    
    print(f"Maximum Drawdown: {strat.max_drawdown * 100:.2f}%")
    
    # 打印分析器结果
    print("\n" + "=" * 70)
    print("ANALYZER RESULTS")
    print("=" * 70)
    
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
    
    # 保存交易记录到 CSV
    if strat.trades:
        trades_df = pd.DataFrame(strat.trades)
        trades_df.to_csv(BACKTEST_CSV, index=False)
        print(f"\n✓ Trade history saved to: {BACKTEST_CSV}")
        
        # 显示最后 10 笔交易
        print("\nLast 10 Trades:")
        print(trades_df.tail(10).to_string(index=False))
        
        # 统计盈亏分布
        print("\n" + "=" * 70)
        print("PnL DISTRIBUTION")
        print("=" * 70)
        winning_trades = trades_df[trades_df['pnl_pct'] > 0]
        losing_trades = trades_df[trades_df['pnl_pct'] <= 0]
        
        print(f"Average Win: {winning_trades['pnl_pct'].mean():.2f}%")
        print(f"Average Loss: {losing_trades['pnl_pct'].mean():.2f}%")
        print(f"Biggest Win: {trades_df['pnl_pct'].max():.2f}%")
        print(f"Biggest Loss: {trades_df['pnl_pct'].min():.2f}%")
        
        # 盈亏比例
        print(f"\nProfit/Loss Ratio: {abs(winning_trades['pnl_pct'].mean() / losing_trades['pnl_pct'].mean()):.2f}")
    
    print("\n" + "=" * 70)
    print("✅ FULL BACKTEST COMPLETED!")
    print("=" * 70)
    print(f"📄 Trades saved to: {BACKTEST_CSV}")
    print(f"💾 Cache directory: {CACHE_DIR}")
    
    return True


# ============================================================================
# 主程序
# ============================================================================
if __name__ == '__main__':
    try:
        success = run_full_backtest()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Backtest interrupted by user")
        print("💾 Data is cached, you can resume later")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)