"""
测试 TradingView Screener API 调用
"""
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_api():
    """测试 TradingView API"""
    try:
        from tradingview_screener import Query, Column
        logger.info("✓ Successfully imported tradingview_screener")
        
        # 测试 1: 最简单的查询
        logger.info("\n=== Test 1: Simple Query ===")
        try:
            query = Query().select('name', 'close').limit(5)
            result = query.get_scanner_data()
            logger.info(f"✓ Test 1 SUCCESS: Got {len(result)} results")
            if result:
                logger.info(f"  First result: {result[0]}")
        except Exception as e:
            logger.error(f"✗ Test 1 FAILED: {e}")
        
        # 测试 2: 带条件查询
        logger.info("\n=== Test 2: Query with conditions ===")
        try:
            query = (
                Query()
                .select('name', 'close', 'volume')
                .where(
                    Column('type').eq('stock')
                )
                .limit(5)
            )
            result = query.get_scanner_data()
            logger.info(f"✓ Test 2 SUCCESS: Got {len(result)} results")
        except Exception as e:
            logger.error(f"✗ Test 2 FAILED: {e}")
        
        # 测试 3: 检查 Column 可用方法
        logger.info("\n=== Test 3: Checking Column methods ===")
        try:
            col = Column('type')
            methods = [m for m in dir(col) if not m.startswith('_')]
            logger.info(f"Available Column methods: {methods}")
        except Exception as e:
            logger.error(f"✗ Test 3 FAILED: {e}")
        
        # 测试 4: 尝试不同的 where 条件
        logger.info("\n=== Test 4: Different where conditions ===")
        
        # 测试 4a: 使用 == 操作符
        try:
            query = Query().select('name').where(Column('type') == 'stock').limit(3)
            result = query.get_scanner_data()
            logger.info(f"✓ Test 4a (== operator) SUCCESS: Got {len(result)} results")
        except Exception as e:
            logger.error(f"✗ Test 4a FAILED: {e}")
        
        # 测试 4b: 使用 .equals()
        try:
            query = Query().select('name').where(Column('type').equals('stock')).limit(3)
            result = query.get_scanner_data()
            logger.info(f"✓ Test 4b (.equals()) SUCCESS: Got {len(result)} results")
        except Exception as e:
            logger.error(f"✗ Test 4b FAILED: {e}")
        
        # 测试 4c: 使用 .eq()
        try:
            query = Query().select('name').where(Column('type').eq('stock')).limit(3)
            result = query.get_scanner_data()
            logger.info(f"✓ Test 4c (.eq()) SUCCESS: Got {len(result)} results")
        except Exception as e:
            logger.error(f"✗ Test 4c FAILED: {e}")
        
        # 测试 5: 完整的美国股票查询
        logger.info("\n=== Test 5: Full US stocks query ===")
        try:
            query = (
                Query()
                .select('name', 'close', 'volume', 'market_cap', 'exchange')
                .where(
                    Column('type').eq('stock'),
                    Column('exchange').is_in(['NASDAQ', 'NYSE', 'AMEX'])
                )
                .order_by('volume', desc=True)
                .limit(10)
            )
            result = query.get_scanner_data()
            logger.info(f"✓ Test 5 SUCCESS: Got {len(result)} US stocks")
            if result:
                for i, stock in enumerate(result[:3]):
                    logger.info(f"  Stock {i+1}: {stock}")
        except Exception as e:
            logger.error(f"✗ Test 5 FAILED: {e}")
        
    except ImportError as e:
        logger.error(f"Failed to import tradingview_screener: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    test_api()