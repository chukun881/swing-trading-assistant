# 🔧 故障排除指南

本文档记录了已知问题及其解决方案。

## 📚 目录

1. [TradingView API 问题](#tradingview-api-问题)
2. [yfinance 数据获取问题](#yfinance-数据获取问题)
3. [Telegram 通知问题](#telegram-通知问题)
4. [IBKR 连接问题](#ibkr-连接问题)
5. [性能优化](#性能优化)

---

## TradingView API 问题

### 问题 1: TradingView API 返回 "Unknown field" 错误

**错误信息：**
```
{"totalCount":0,"error":"Unknown field \"market_cap\"","data":null}
```

**原因：** TradingView Screener API 不支持 `market_cap` 字段。

**解决方案：**
- 从 `.select()` 中移除 `market_cap` 字段
- 使用支持的字段：`name`, `close`, `volume`, `exchange`, `ticker`

**示例：**
```python
# ❌ 错误
query = Query().select('name', 'close', 'volume', 'market_cap', 'exchange')

# ✅ 正确
query = Query().select('name', 'close', 'volume', 'exchange')
```

### 问题 2: TradingView API 返回 "Column object has no attribute" 错误

**错误信息：**
```
'Column' object has no attribute 'equals'
'Column' object has no attribute 'greater_than'
'Column' object has no attribute 'is_in'
```

**原因：** 使用了不存在的 Column 方法。

**解决方案：** 使用正确的操作符和方法

**可用的 Column 方法：**
```python
# ✅ 正确的用法
Column('type') == 'stock'                    # 使用 == 操作符
Column('volume') >= 1000000                  # 使用 >= 操作符
Column('exchange').isin(['NASDAQ', 'NYSE'])  # 使用 .isin() 方法
Column('name').like('AAPL')                  # 使用 .like() 方法

# ❌ 错误的用法
Column('type').equals('stock')               # 方法不存在
Column('volume').greater_than(1000000)       # 方法不存在
Column('exchange').is_in(['NASDAQ', 'NYSE']) # 方法不存在
```

**完整的 Column 方法列表：**
- `above_pct`, `below_pct`, `between`, `between_pct`
- `crosses`, `crosses_above`, `crosses_below`
- `empty`, `has`, `has_none_of`
- `in_day_range`, `in_month_range`, `in_week_range`, `isin`, `like`
- `not_between`, `not_between_pct`, `not_empty`, `not_in`, `not_like`

### 问题 3: order_by() 参数错误

**错误信息：**
```
order_by() got an unexpected keyword argument 'desc'
```

**原因：** `order_by()` 方法不支持 `desc` 参数。

**解决方案：** 移除 `desc` 参数
```python
# ❌ 错误
query.order_by('volume', desc=True)

# ✅ 正确
query.order_by('volume')
```

### 问题 4: 'int' object has no attribute 'get'

**错误信息：**
```
'int' object has no attribute 'get'
```

**原因：** TradingView API 返回的是 tuple，不是列表。

**解决方案：** 正确处理返回值
```python
result = query.get_scanner_data()

# ✅ 正确处理
if isinstance(result, tuple) and len(result) == 2:
    total, df = result
    stocks = df.to_dict('records')
    
    # 提取纯股票代码（去掉交易所前缀）
    for stock in stocks:
        if 'ticker' in stock:
            ticker = stock['ticker']
            if ':' in ticker:
                stock['name'] = ticker.split(':')[1]
            else:
                stock['name'] = ticker
```

---

## yfinance 数据获取问题

### 问题 1: 马来西亚股票数据获取失败

**错误信息：**
```
HTTP Error 404: {"quoteSummary":{"result":null,"error":{"code":"Not Found"}}}
```

**原因：** 股票代码格式不正确。

**解决方案：** 使用正确的 yfinance 代码格式

**马来西亚股票代码格式：**
- ✅ `1155.KL` - Maybank（使用股票代码 + .KL）
- ✅ `1023.KL` - CIMB
- ✅ `1295.KL` - Public Bank
- ❌ `MAYBANK.KL` - 不存在
- ❌ `CIMB.KL` - 不存在

**如何找到正确的代码：**
1. 访问 [Yahoo Finance](https://finance.yahoo.com/)
2. 搜索股票名称（例如：Maybank）
3. 查看地址栏中的代码（例如：`1155.KL`）

### 问题 2: 美国股票被错误添加 .KL 后缀

**症状：** AAPL 被转换为 AAPL.KL，导致数据获取失败。

**原因：** 简单的字符长度判断无法正确区分美国和马来西亚股票。

**解决方案：** 使用 `market` 参数明确指定市场
```python
# 在 get_stock_list_with_data 中
us_stocks = market_data['us'][:max_stocks_per_market]
for stock in us_stocks:
    symbol = stock.get('name', '')
    df = get_stock_historical_data(symbol, market='US')  # 明确指定市场
    
my_stocks = market_data['malaysia'][:max_stocks_per_market]
for stock in my_stocks:
    symbol = stock.get('name', '')
    df = get_stock_historical_data(symbol, market='Malaysia')  # 明确指定市场
```

### 问题 3: No data found for symbol

**错误信息：**
```
$5686.KL: possibly delisted; no data found
```

**原因：** 股票可能已退市或代码不正确。

**解决方案：**
1. 验证股票代码是否正确
2. 在 Yahoo Finance 上搜索股票
3. 系统会自动跳过这些股票，继续处理其他股票

---

## Telegram 通知问题

### 问题 1: Event loop is closed 错误

**错误信息：**
```
RuntimeError: Event loop is closed
```

**原因：** 异步事件循环管理不当。

**解决方案：** 完整的事件循环管理（已在代码中实现）

**影响：** 这个错误不会影响消息发送，消息最终会成功发送。

### 问题 2: Telegram Bot Token 无效

**错误信息：**
```
Telegram API error: Unauthorized
```

**原因：** Bot Token 不正确或已被撤销。

**解决方案：**
1. 联系 @BotFather 创建新 bot
2. 获取新的 Bot Token
3. 更新 `config/.env` 文件：
```bash
TELEGRAM_BOT_TOKEN=your_new_bot_token
```

### 问题 3: 找不到 Chat ID

**症状：** 消息无法发送，提示 chat_id 无效。

**解决方案：**

**方法 1: 使用 API 获取**
```bash
# 替换 YOUR_BOT_TOKEN
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

**方法 2: 使用 Python 脚本**
```python
import requests

token = "YOUR_BOT_TOKEN"
url = f"https://api.telegram.org/bot{token}/getUpdates"
response = requests.get(url)
print(response.json())
```

**方法 3: 发送消息后查看日志**
```bash
# 运行程序，在日志中查找 chat_id
python3 src/main.py
```

---

## IBKR 连接问题

### 问题 1: 无法连接到 IB TWS

**错误信息：**
```
Failed to connect to IB TWS: Event loop is closed
```

**原因：** IB TWS 客户端未运行或 API 未启用。

**解决方案：**

1. **启动 TWS 客户端**
   - 打开 Interactive Brokers TWS 应用
   - 登录您的账户

2. **启用 API**
   - File → Global Configuration → API → Settings
   - 勾选 "Enable ActiveX and Socket Clients"
   - 设置 Socket Port（默认 7496）
   - 勾选 "Allow connections from localhost"

3. **更新配置**
   ```bash
   # config/.env
   IB_HOST=127.0.0.1
   IB_PORT=7496
   IB_CLIENT_ID=1
   ```

**注意：** 即使 IBKR 连接失败，程序仍会继续运行并扫描市场。

### 问题 2: RuntimeWarning: coroutine was never awaited

**错误信息：**
```
RuntimeWarning: coroutine 'IB.connectAsync' was never awaited
```

**原因：** IBKR 异步连接方法未正确处理。

**影响：** 仅影响 IBKR 连接，不影响其他功能。

---

## 性能优化

### 问题 1: 扫描速度较慢

**症状：** 扫描 150 只股票需要 30 秒以上。

**解决方案：**

1. **减少扫描股票数量**
   ```yaml
   # config/config.yaml
   markets:
     us:
       max_stocks: 50  # 减少从 100 到 50
     malaysia:
       max_stocks: 25  # 减少从 50 到 25
   ```

2. **增加最小成交量过滤**
   ```yaml
   markets:
     us:
       min_volume: 5000000  # 增加从 1M 到 5M
     malaysia:
       min_volume: 2000000  # 增加从 500K 到 2M
   ```

3. **使用并发请求（未来改进）**
   - 实现并发数据获取
   - 预计可将扫描时间减少到 10 秒以内

### 问题 2: 频繁的 API 请求被限制

**症状：** 偶尔出现 429 Too Many Requests 错误。

**解决方案：**
- 代码已添加延迟（每个请求 0.5 秒）
- 如果仍然遇到限制，增加延迟时间：
  ```python
  # src/data/tradingview.py
  time.sleep(1.0)  # 从 0.5 增加到 1.0
  ```

---

## 调试技巧

### 1. 启用 DEBUG 日志

```python
# src/main.py
def setup_logging(log_level: str = 'DEBUG'):  # 改为 DEBUG
```

### 2. 测试 TradingView API

```bash
# 运行测试脚本
python3 test_tradingview_api.py
```

### 3. 测试数据获取

```python
# 临时测试脚本
from src.data.tradingview import get_stock_historical_data

df = get_stock_historical_data('AAPL', market='US')
print(df.head())

df = get_stock_historical_data('1155.KL', market='Malaysia')
print(df.head())
```

### 4. 检查配置

```bash
# 查看配置文件
cat config/config.yaml
cat config/.env
```

---

## 常见问题解答

### Q: TradingView API 是免费的吗？

A: 是的，TradingView Screener API 是免费的，但有速率限制。

### Q: yfinance API 是免费的吗？

A: 是的，yfinance 是开源免费的，但请遵守 Yahoo Finance 的服务条款。

### Q: 如何获取更多股票？

A: 调整配置文件中的 `max_stocks` 和 `min_volume` 参数。

### Q: 如何添加新的市场？

A: 需要修改 `src/data/tradingview.py` 添加新的市场扫描函数。

### Q: IBKR 是必需的吗？

A: 不是必需的。如果没有 IBKR 账户，程序仍会扫描市场并发送信号。

---

## 获取帮助

如果以上解决方案无法解决您的问题：

1. 查看日志文件：`logs/trading_assistant_YYYYMMDD.log`
2. 运行测试脚本验证各个模块
3. 提交 Issue 到 GitHub 仓库

---

## 📝 更新日志

### 2026-04-23
- ✅ 修复 TradingView Screener API 调用语法
- ✅ 修复 TradingView API 返回的 tuple 数据结构
- ✅ 修复股票代码后缀逻辑（添加 market 参数）
- ✅ 修复马来西亚股票代码格式
- ✅ 修复 Telegram 异步事件循环问题
- ✅ 成功实现动态市场扫描（100 US + 50 MY 股票）

---

**最后更新：** 2026-04-23