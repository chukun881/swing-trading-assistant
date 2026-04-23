"""
详细测试 TradingView Screener API
"""
import logging
import sys

# 启用 DEBUG 日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_with_debug():
    """使用 DEBUG 日志测试 API"""
    try:
        from tradingview_screener import Query, Column
        
        print("\n=== 测试 1: 完整的美国股票查询 ===")
        print("Query:")
        print("  Column('type') == 'stock'")
        print("  Column('exchange').isin(['NASDAQ', 'NYSE', 'AMEX'])")
        print("  Column('volume') >= 1000000")
        print("  .order_by('volume')")
        print("  .limit(100)")
        print()
        
        query = (
            Query()
            .select('name', 'close', 'volume', 'market_cap', 'exchange')
            .where(
                Column('type') == 'stock',
                Column('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                Column('volume') >= 1000000
            )
            .order_by('volume')
            .limit(100)
        )
        
        print("Executing query...")
        stocks = query.get_scanner_data()
        print(f"\n✓ SUCCESS! Got {len(stocks)} stocks")
        if stocks:
            print(f"First stock: {stocks[0]}")
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("Detailed TradingView Screener API Test")
    print("=" * 70)
    
    success = test_with_debug()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ API WORKS!")
    else:
        print("✗ API FAILED - Using fallback")
    print("=" * 70)