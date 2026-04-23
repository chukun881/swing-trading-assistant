"""
测试 TradingView Malaysia API
验证能否获取真实的 Bursa Malaysia 股票
"""
import requests
import json

def test_malaysia_api():
    """测试 TradingView Malaysia 端点"""
    
    url = "https://scanner.tradingview.com/malaysia/scan"
    
    payload = {
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "exchange", "operation": "equal", "right": "BURSA"}
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
        "range": [0, 50]
    }
    
    print("=" * 60)
    print("Testing TradingView Malaysia API")
    print("=" * 60)
    
    try:
        print(f"\n📡 POST request to: {url}")
        print(f"📊 Requesting top 50 stocks by volume...")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📦 Response structure keys: {data.keys()}")
            
            if 'data' in data:
                stocks = data['data']
                print(f"\n🎯 Total stocks retrieved: {len(stocks)}")
                
                print("\n" + "=" * 60)
                print("First 20 stocks:")
                print("=" * 60)
                
                for i, stock in enumerate(stocks[:20]):
                    # stock 格式: [symbol, close, volume, exchange, market_cap]
                    if len(stock) >= 4:
                        symbol = stock[0]
                        close = stock[1]
                        volume = stock[2]
                        exchange = stock[3]
                        
                        print(f"\n{i+1}. {symbol}")
                        print(f"   Close: {close}")
                        print(f"   Volume: {volume}")
                        print(f"   Exchange: {exchange}")
                
                print("\n" + "=" * 60)
                print("📊 Analysis:")
                print("=" * 60)
                
                # 分析股票代码格式
                numeric_count = 0
                alpha_count = 0
                mixed_count = 0
                
                for stock in stocks:
                    symbol = stock[0]
                    if symbol.isdigit():
                        numeric_count += 1
                    elif symbol.replace('.', '').isdigit():
                        numeric_count += 1
                    elif symbol.isalpha():
                        alpha_count += 1
                    else:
                        mixed_count += 1
                
                print(f"✓ Numeric codes (e.g., 1155): {numeric_count}")
                print(f"✓ Alphabetic codes (e.g., MAYBANK): {alpha_count}")
                print(f"✓ Mixed codes: {mixed_count}")
                
                # 检查是否有 OTC 股票
                otc_stocks = [s[0] for s in stocks if any(x in s[0].upper() for x in ['FIELF', 'AHGDS', 'DLGEF', 'BMXMF'])]
                
                if otc_stocks:
                    print(f"\n❌ Found OTC stocks (BAD): {otc_stocks}")
                else:
                    print(f"\n✅ No OTC stocks found (GOOD!)")
                
                return True
            else:
                print(f"\n❌ No 'data' key in response")
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
                return False
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_malaysia_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - TradingView Malaysia API works!")
    else:
        print("❌ TEST FAILED - Need to troubleshoot")
    print("=" * 60)