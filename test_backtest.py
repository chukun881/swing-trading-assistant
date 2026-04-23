"""
快速测试回测引擎
使用少量股票和较短时间范围进行测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtest_engine import run_backtest, get_russell1000_tickers, download_data
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_quick():
    """快速测试"""
    print("=" * 60)
    print("QUICK BACKTEST TEST")
    print("=" * 60)
    
    # 使用更短的时间范围和少量股票
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')  # 6个月
    
    # 只测试前 5 只股票
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"\nTest Configuration:")
    print(f"  Date Range: {start_date} to {end_date}")
    print(f"  Stocks: {tickers}")
    print(f"  Initial Capital: $10,000")
    
    try:
        # 修改 backtest_engine 中的函数以使用我们的参数
        from src.backtest_engine import download_data
        import backtrader as bt
        
        # 下载测试数据
        print(f"\nDownloading data for {len(tickers)} stocks...")
        data_dict = download_data(tickers, start_date, end_date)
        
        if not data_dict:
            print("❌ No data downloaded!")
            return False
        
        print(f"✓ Downloaded {len(data_dict)} stocks")
        
        # 创建 Cerebro
        cerebro = bt.Cerebro()
        
        # 添加策略
        from src.backtest_engine import SwingTradingStrategy
        cerebro.addstrategy(SwingTradingStrategy)
        
        # 添加数据
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
        
        # 设置佣金（使用自定义佣金类）
        from src.backtest_engine import IBKRCommission
        cerebro.broker.addcommissioninfo(IBKRCommission())
        
        # 设置初始资金
        cerebro.broker.setcash(10000.0)
        
        # 运行回测
        print(f"\nStarting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
        results = cerebro.run()
        
        strat = results[0]
        
        print(f"\nFinal Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
        print(f"Total Trades: {strat.trade_count}")
        print(f"Winning Trades: {strat.winning_trades}")
        print(f"Losing Trades: {strat.losing_trades}")
        
        if strat.trade_count > 0:
            win_rate = strat.winning_trades / strat.trade_count * 100
            print(f"Win Rate: {win_rate:.2f}%")
        
        print(f"Maximum Drawdown: {strat.max_drawdown * 100:.2f}%")
        
        print("\n" + "=" * 60)
        print("✅ BACKTEST ENGINE WORKING!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_quick()
    sys.exit(0 if success else 1)