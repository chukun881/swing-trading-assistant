"""
测试修复后的 TradingView Screener API
"""
import logging
from tradingview_screener import Query, Column

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fixed_us_methods():
    """测试修复后的美国股票获取方法"""
    
    print("\n=== 测试方法 1: 正确的 API (== 操作符 + isin) ===")
    try:
        query = (
            Query()
            .select('name', 'close', 'volume', 'market_cap', 'exchange')
            .where(
                Column('type') == 'stock',
                Column('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
                Column('volume') >= 1000000
            )
            .order_by('volume', desc=True)
            .limit(10)
        )
        stocks = query.get_scanner_data()
        print(f"✓ 方法 1 成功！获取了 {len(stocks)} 只股票")
        if stocks:
            print(f"  示例股票: {stocks[0]}")
    except Exception as e:
        print(f"✗ 方法 1 失败: {e}")
    
    print("\n=== 测试方法 2: 简化查询（只过滤类型） ===")
    try:
        query = (
            Query()
            .select('name', 'close', 'volume', 'market_cap', 'exchange')
            .where(
                Column('type') == 'stock'
            )
            .order_by('volume', desc=True)
            .limit(10)
        )
        stocks = query.get_scanner_data()
        print(f"✓ 方法 2 成功！获取了 {len(stocks)} 只股票")
        if stocks:
            print(f"  示例股票: {stocks[0]}")
    except Exception as e:
        print(f"✗ 方法 2 失败: {e}")
    
    print("\n=== 测试方法 3: 使用 .in_() 方法 ===")
    try:
        query = (
            Query()
            .select('name', 'close', 'volume', 'market_cap', 'exchange')
            .where(
                Column('type') == 'stock',
                Column('exchange').in_(['NASDAQ', 'NYSE'])
            )
            .order_by('volume', desc=True)
            .limit(10)
        )
        stocks = query.get_scanner_data()
        print(f"✓ 方法 3 成功！获取了 {len(stocks)} 只股票")
        if stocks:
            print(f"  示例股票: {stocks[0]}")
    except Exception as e:
        print(f"✗ 方法 3 失败: {e}")


def test_fixed_malaysia_methods():
    """测试修复后的马来西亚股票获取方法"""
    
    print("\n=== 测试马来西亚方法 1: 正确的 API (== 操作符) ===")
    try:
        query = (
            Query()
            .select('name', 'close', 'volume', 'market_cap', 'exchange')
            .where(
                Column('type') == 'stock',
                Column('exchange') == 'BURSA',
                Column('volume') >= 500000
            )
            .order_by('volume', desc=True)
            .limit(10)
        )
        stocks = query.get_scanner_data()
        print(f"✓ 马来西亚方法 1 成功！获取了 {len(stocks)} 只股票")
        if stocks:
            print(f"  示例股票: {stocks[0]}")
    except Exception as e:
        print(f"✗ 马来西亚方法 1 失败: {e}")
    
    print("\n=== 测试马来西亚方法 2: 简化查询 ===")
    try:
        query = (
            Query()
            .select('name', 'close', 'volume', 'market_cap', 'exchange')
            .where(
                Column('type') == 'stock'
            )
            .order_by('volume', desc=True)
            .limit(10)
        )
        stocks = query.get_scanner_data()
        print(f"✓ 马来西亚方法 2 成功！获取了 {len(stocks)} 只股票")
        if stocks:
            print(f"  示例股票: {stocks[0]}")
    except Exception as e:
        print(f"✗ 马来西亚方法 2 失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试修复后的 TradingView Screener API")
    print("=" * 60)
    
    test_fixed_us_methods()
    test_fixed_malaysia_methods()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)