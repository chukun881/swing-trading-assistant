"""
测试 TradingView API 返回的数据格式
"""
from tradingview_screener import Query, Column

# 测试方法 1
query = (
    Query()
    .select('name', 'close', 'volume', 'exchange')
    .where(
        Column('type') == 'stock',
        Column('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
        Column('volume') >= 1000000
    )
    .order_by('volume')
    .limit(5)
)

stocks = query.get_scanner_data()

print(f"Type of result: {type(stocks)}")
print(f"Length: {len(stocks)}")
print(f"\nFirst element type: {type(stocks[0])}")
print(f"First element: {stocks[0]}")

if len(stocks) > 1:
    print(f"\nSecond element type: {type(stocks[1])}")
    print(f"Second element: {stocks[1]}")