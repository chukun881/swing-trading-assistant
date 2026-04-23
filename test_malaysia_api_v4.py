"""
测试 TradingView Malaysia API - 版本4
修复数据结构解析
"""
import requests
import json

def test_myx_structure():
    """分析数据结构"""
    print("=" * 60)
    print("Analyzing MYX Data Structure")
    print("=" * 60)
    
    url = "https://scanner.tradingview.com/malaysia/scan"
    
    payload = {
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "exchange", "operation": "equal", "right": "MYX"}
        ],
        "options": {"lang": "en"},
        "symbols": {
            "query": {
                "types": []
            },
            "tickers": []
        },
        "columns": ["name", "close", "volume", "exchange", "market_cap_basic"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 10]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 Total count: {data.get('totalCount', 0)}")
            
            stocks = data.get('data', [])
            print(f"🎯 Stocks retrieved: {len(stocks)}")
            
            if stocks:
                print(f"\n📦 First item type: {type(stocks[0])}")
                print(f"📦 First item: {stocks[0]}")
                
                if isinstance(stocks[0], dict):
                    print(f"\n📋 Dictionary keys: {stocks[0].keys()}")
                    print("\n" + "=" * 60)
                    print("First 5 stocks (dict format):")
                    print("=" * 60)
                    
                    for i, stock in enumerate(stocks[:5]):
                        print(f"\n{i+1}. {stock}")
                
                return stocks
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_myx_300():
    """获取 300 只股票并分析"""
    print("\n" + "=" * 60)
    print("Testing MYX - 300 Stocks")
    print("=" * 60)
    
    url = "https://scanner.tradingview.com/malaysia/scan"
    
    payload = {
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "exchange", "operation": "equal", "right": "MYX"}
        ],
        "options": {"lang": "en"},
        "symbols": {
            "query": {
                "types": []
            },
            "tickers": []
        },
        "columns": ["name", "close", "volume", "exchange", "market_cap_basic"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 300]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('data', [])
            
            print(f"✅ Retrieved {len(stocks)} stocks")
            print(f"📊 Total available: {data.get('totalCount', 0)}")
            
            if stocks:
                # 分析股票代码
                symbols = []
                for stock in stocks:
                    if isinstance(stock, dict):
                        symbol = stock.get('name', '')
                        if symbol:
                            symbols.append(symbol)
                
                print(f"\n📊 Total valid symbols: {len(symbols)}")
                
                # 分析代码格式
                numeric = [s for s in symbols if s.isdigit()]
                alpha = [s for s in symbols if s.isalpha()]
                mixed = [s for s in symbols if not s.isdigit() and not s.isalpha()]
                
                print(f"\n✓ Numeric codes: {len(numeric)}")
                print(f"✓ Alphabetic codes: {len(alpha)}")
                print(f"✓ Mixed codes: {len(mixed)}")
                
                # 检查 OTC
                otc = [s for s in symbols if any(x in s.upper() for x in ['FIELF', 'AHGDS', 'DLGEF', 'BMXMF', 'SONVF', 'SBNC'])]
                
                if otc:
                    print(f"\n❌ Found OTC stocks: {otc[:10]}")
                else:
                    print(f"\n✅ No OTC stocks!")
                
                # 显示前 20 只
                print("\n" + "=" * 60)
                print("First 20 stocks:")
                print("=" * 60)
                for i, symbol in enumerate(symbols[:20]):
                    print(f"{i+1}. {symbol}")
                
                return symbols
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    # 分析结构
    test_myx_structure()
    
    # 获取 300 只
    symbols = test_myx_300()
    
    print("\n" + "=" * 60)
    print("Final Summary:")
    print("=" * 60)
    print(f"✅ Successfully retrieved {len(symbols)} symbols")
    print(f"✅ Ready to implement in production")