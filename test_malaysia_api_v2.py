"""
测试 TradingView Malaysia API - 版本2
尝试不同的过滤策略
"""
import requests
import json

def test_strategy_1():
    """策略1: 只过滤类型，不过滤交易所"""
    print("\n" + "=" * 60)
    print("Strategy 1: Only filter by type (stock)")
    print("=" * 60)
    
    url = "https://scanner.tradingview.com/malaysia/scan"
    
    payload = {
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"}
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
        "range": [0, 20]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('data', [])
            print(f"✅ Retrieved {len(stocks)} stocks")
            
            if stocks:
                print("\nFirst 10 stocks:")
                for i, stock in enumerate(stocks[:10]):
                    symbol = stock[0]
                    exchange = stock[3]
                    print(f"{i+1}. {symbol} - Exchange: {exchange}")
                
                # 检查 exchange 类型
                exchanges = set()
                for stock in stocks:
                    if len(stock) >= 4:
                        exchanges.add(stock[3])
                print(f"\n📊 Exchanges found: {exchanges}")
                
                return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_strategy_2():
    """策略2: 使用不同的 exchange 名称"""
    print("\n" + "=" * 60)
    print("Strategy 2: Try different exchange names")
    print("=" * 60)
    
    url = "https://scanner.tradingview.com/malaysia/scan"
    
    # 尝试不同的 exchange 名称
    exchange_names = ["BURSA", "XKLS", "KLSE", "MYX", "KLS", "Bursa"]
    
    for exchange in exchange_names:
        payload = {
            "filter": [
                {"left": "type", "operation": "equal", "right": "stock"},
                {"left": "exchange", "operation": "equal", "right": exchange}
            ],
            "options": {"lang": "en"},
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": ["name", "close", "volume", "exchange"],
            "sort": {"sortBy": "volume", "sortOrder": "desc"},
            "range": [0, 10]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('data', [])
                if stocks:
                    print(f"✅ Exchange '{exchange}' works! Got {len(stocks)} stocks")
                    print(f"   Example: {stocks[0][0]}")
                    return exchange, stocks
                else:
                    print(f"❌ Exchange '{exchange}': No stocks")
        except:
            pass
    
    return None, []


def test_strategy_3():
    """策略3: 不使用任何过滤"""
    print("\n" + "=" * 60)
    print("Strategy 3: No filters at all")
    print("=" * 60)
    
    url = "https://scanner.tradingview.com/malaysia/scan"
    
    payload = {
        "filter": [],
        "options": {"lang": "en"},
        "symbols": {
            "query": {
                "types": []
            },
            "tickers": []
        },
        "columns": ["name", "close", "volume", "exchange", "market_cap_basic", "type"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 30]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('data', [])
            print(f"✅ Retrieved {len(stocks)} items (all types)")
            
            # 分析类型
            types = set()
            exchanges = set()
            
            for item in stocks:
                if len(item) >= 6:
                    types.add(item[5])
                    exchanges.add(item[3])
            
            print(f"\n📊 Types found: {types}")
            print(f"📊 Exchanges found: {exchanges}")
            
            # 只显示股票
            print("\nStocks only:")
            stock_count = 0
            for item in stocks:
                if len(item) >= 6 and item[5] == 'stock':
                    symbol = item[0]
                    exchange = item[3]
                    print(f"  {symbol} - {exchange}")
                    stock_count += 1
                    if stock_count >= 10:
                        break
            
            return stocks
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    print("=" * 60)
    print("Testing TradingView Malaysia API - Version 2")
    print("=" * 60)
    
    # 策略1
    test_strategy_1()
    
    # 策略2
    working_exchange, stocks = test_strategy_2()
    
    # 策略3
    all_items = test_strategy_3()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if working_exchange:
        print(f"✅ Working exchange: {working_exchange}")
    else:
        print("⚠️ No working exchange found")
    
    if all_items:
        print(f"✅ Total items retrieved: {len(all_items)}")