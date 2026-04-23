"""
快速测试新架构 - 只测试几只股票
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analysis.breakout import add_signals_to_dataframe, calculate_indicators_batch
from src.backtest_engine import SwingTradingStrategy, IBKRCommission, SignalPandasData
from datetime import datetime, timedelta
import backtrader as bt
import pandas as pd
import yfinance as yf

print("=" * 70)
print("新架构快速测试")
print("=" * 70)

# 测试配置
test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

print(f"\n测试配置:")
print(f"  股票: {test_tickers}")
print(f"  日期范围: {start_date} 到 {end_date}")
print(f"  初始资金: $10,000")

# 下载市场数据
print(f"\n1. 下载市场数据...")
spy_df = yf.download('SPY', start=start_date, end=end_date, progress=False)
vix_df = yf.download('^VIX', start=start_date, end=end_date, progress=False)

if isinstance(spy_df.columns, pd.MultiIndex):
    spy_df.columns = spy_df.columns.get_level_values(0)
if isinstance(vix_df.columns, pd.MultiIndex):
    vix_df.columns = vix_df.columns.get_level_values(0)

spy_df.index = pd.to_datetime(spy_df.index)
vix_df.index = pd.to_datetime(vix_df.index)
spy_df.columns = [str(col).lower() for col in spy_df.columns]
vix_df.columns = [str(col).lower() for col in vix_df.columns]

print(f"  ✓ SPY: {len(spy_df)} 天")
print(f"  ✓ VIX: {len(vix_df)} 天")

# 下载股票数据
print(f"\n2. 下载股票数据...")
data_dict = {}
for ticker in test_tickers:
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index = pd.to_datetime(df.index)
            df.columns = [str(col).lower() for col in df.columns]
            data_dict[ticker] = df
            print(f"  ✓ {ticker}: {len(df)} 天")
        else:
            print(f"  ✗ {ticker}: 无数据")
    except Exception as e:
        print(f"  ✗ {ticker}: {e}")

# 使用 breakout.py 添加信号
print(f"\n3. 使用 breakout.py 添加指标和信号...")
data_dict = calculate_indicators_batch(data_dict, spy_df, vix_df)
print(f"  ✓ 信号已添加到 {len(data_dict)} 只股票")

# 检查信号列
print(f"\n4. 验证信号列...")
for ticker in test_tickers:
    if ticker in data_dict:
        df = data_dict[ticker]
        buy_signals = df['Buy_Signal'].sum()
        sell_signals = df['Sell_Signal'].sum()
        print(f"  {ticker}: Buy_Signal={buy_signals}, Sell_Signal={sell_signals}")
        
        # 显示最后5天的信号
        print(f"    最近5天:")
        recent = df[['close', 'rsi', 'Buy_Signal', 'Sell_Signal']].tail(5)
        for idx, row in recent.iterrows():
            buy = "BUY" if row['Buy_Signal'] else ""
            sell = "SELL" if row['Sell_Signal'] else ""
            print(f"      {idx.strftime('%Y-%m-%d')}: Close=${row['close']:.2f}, RSI={row['rsi']:.1f}, [{buy}{sell}]")

# 运行回测
print(f"\n5. 运行回测...")
cerebro = bt.Cerebro()
cerebro.addstrategy(SwingTradingStrategy)

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

cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
cerebro.broker.addcommissioninfo(IBKRCommission())
cerebro.broker.setcash(10000.0)

print(f"  初始资金: ${cerebro.broker.getvalue():,.2f}")

results = cerebro.run()
strat = results[0]

print(f"\n6. 回测结果:")
print(f"  初始资金: $10,000.00")
print(f"  最终资金: ${cerebro.broker.getvalue():,.2f}")
print(f"  总收益: {(cerebro.broker.getvalue() - 10000) / 10000 * 100:+.2f}%")
print(f"  总交易: {strat.trade_count}")
print(f"  盈利: {strat.winning_trades}")
print(f"  亏损: {strat.losing_trades}")
if strat.trade_count > 0:
    print(f"  胜率: {strat.winning_trades / strat.trade_count * 100:.2f}%")
print(f"  最大回撤: {strat.max_drawdown * 100:.2f}%")

if strat.trades:
    print(f"\n7. 交易记录:")
    trades_df = pd.DataFrame(strat.trades)
    print(trades_df.to_string(index=False))

print("\n" + "=" * 70)
print("✅ 新架构测试完成!")
print("=" * 70)