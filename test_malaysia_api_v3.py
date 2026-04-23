"""
测试 TradingView Malaysia API - 版本3
使用 MYX 交易所
"""
import requests
import json

def test_myx_detailed():
    """详细测试 MYX 交易所"""
    print("=" * 60)
    print("Testing MYX Exchange - Detailed")
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
        "columns": ["name", "close", "volume", "exchange", "market_cap_basic", "type"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 50]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"\n✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📦 Response keys: {data.keys()}")
            print(f"📊 Total count: {data.get('totalCount', 0)}")
            
            stocks = data.get('data', [])
            print(f"🎯 Stocks retrieved: {len(stocks)}")
            
            if stocks:
                print("\n" + "=" * 60)
                print("First 20 stocks:")
                print("=" * 60)
                
                for i, stock in enumerate(stocks[:20]):
                    # stock 格式: [symbol, close, volume, exchange, market_cap, type]
                    if len(stock) >= 6:
                        symbol = stock[0]
                        close = stock[1]
                        volume = stock[2]
                        exchange = stock[3]
                        market_cap = stock[4]
                        stype = stock[5]
                        
                        print(f"\n{i+1}. {symbol}")
                        print(f"   Close: {close}")
                        print(f"   Volume: {volume}")
                        print(f"   Exchange: {exchange}")
                        print(f"   Market Cap: {market_cap}")
                        print(f"   Type: {stype}")
                
                # 分析股票代码
                print("\n" + "=" * 60)
                print("Stock Code Analysis:")
                print("=" * 60)
                
                numeric = 0
                alpha = 0
                mixed = 0
                
                for stock in stocks:
                    symbol = stock[0]
                    if symbol.isdigit():
                        numeric += 1
                    elif symbol.isalpha():
                        alpha += 1
                    else:
                        mixed += 1
                
                print(f"✓ Numeric (e.g., 1155): {numeric}")
                print(f"✓ Alphabetic (e.g., MAYBANK): {alpha}")
                print(f"✓ Mixed: {mixed}")
                
                # 检查 OTC
                otc = [s[0] for s in stocks if any(x in s[0].upper() for x in ['FIELF', 'AHGDS', 'DLGEF', 'BMXMF', 'SONVF', 'SBNC'])]
                
                if otc:
                    print(f"\n❌ Found OTC stocks: {otc}")
                else:
                    print(f"\n✅ No OTC stocks!")
                
                return stocks
            else:
                print("❌ No stocks found")
                return []
        else:
            print(f"❌ Failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_myx_300_stocks():
    """测试获取 300 只股票"""
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
        "columns": ["name", "close", "volume", "exchange"],
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
            
            return stocks
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    # 详细测试
    stocks = test_myx_detailed()
    
    # 测试 300 只
    stocks_300 = test_myx_300_stocks()
    
    print("\n" + "=" * 60)
    print("Final Summary:")
    print("=" * 60)
    print(f"✅ Can retrieve: {len(stocks_300)} stocks from MYX")
    print(f"✅ Strategy: Use 'MYX' as exchange filter")