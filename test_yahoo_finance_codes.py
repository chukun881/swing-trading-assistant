"""
测试 Yahoo Finance 是否支持字母代码
"""
import yfinance as yf

def test_malaysia_codes():
    """测试不同的马来西亚股票代码格式"""
    
    # 测试代码
    test_codes = [
        # 字母代码
        'ZETRIX.KL',
        'AAX.KL',
        'TOPGLOV.KL',
        'DNEX.KL',
        'ASTRO.KL',
        # 数字代码
        '1155.KL',  # Maybank
        '1023.KL',  # CIMB
        '1295.KL',  # Public Bank
    ]
    
    print("=" * 60)
    print("Testing Yahoo Finance Malaysia Codes")
    print("=" * 60)
    
    for code in test_codes:
        print(f"\n📊 Testing: {code}")
        try:
            ticker = yf.Ticker(code)
            df = ticker.history(period='5d', interval='1d')
            
            if df.empty:
                print(f"   ❌ No data found")
            else:
                print(f"   ✅ Data retrieved!")
                print(f"   Rows: {len(df)}")
                print(f"   Latest close: {df['Close'].iloc[-1]:.2f}")
                print(f"   Latest volume: {df['Volume'].iloc[-1]:,}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_malaysia_codes()
