# 配置指南 (Configuration Guide)

## API Keys 配置位置

所有 API Keys 和敏感配置都应该放在 `config/.env` 文件中。

### 配置文件位置
```
swing-trading-assistant/
├── config/
│   ├── .env          # 🔒 敏感配置（不提交到 Git）
│   ├── .env.example  # 配置模板（提交到 Git）
│   ├── config.yaml   # 通用配置
│   └── malaysia_ticker_mapping.json  # 马来西亚股票映射
```

---

## 1. 创建/编辑 `.env` 文件

编辑 `config/.env` 文件，添加你的 API Keys：

```bash
# ============================================================================
# Telegram Bot 配置
# ============================================================================
# 如何获取：https://core.telegram.org/bots#6-botfather
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# 如何获取：给 @userinfobot 发送消息
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# ============================================================================
# TradingView 配置（如需使用 TradingView API）
# ============================================================================
# TradingView Cookie（如果需要）
TRADINGVIEW_COOKIE=your_tradingview_cookie_here

# ============================================================================
# Interactive Brokers (IBKR) 配置
# ============================================================================
# IBKR TWS 或 IB Gateway 连接信息
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # TWS: 7497, IB Gateway: 4001 (Paper Trading)
IBKR_CLIENT_ID=1

# ============================================================================
# 数据源配置
# ============================================================================
# Yahoo Finance（免费，无需 API Key）
# Alpha Vantage（可选）
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# ============================================================================
# 应用配置
# ============================================================================
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 时区
TIMEZONE=Asia/Kuala_Lumpur

# 市场开盘时间（用于判断交易时间）
MARKET_OPEN_TIME=09:30
MARKET_CLOSE_TIME=16:00
```

---

## 2. 获取 API Keys 的步骤

### Telegram Bot Token
1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按照提示设置机器人名称和用户名
4. BotFather 会返回一个 API Token
5. 将 Token 复制到 `.env` 文件的 `TELEGRAM_BOT_TOKEN`

### Telegram Chat ID
1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息给这个机器人
3. 它会返回你的 Chat ID
4. 将 Chat ID 复制到 `.env` 文件的 `TELEGRAM_CHAT_ID`

### IBKR 配置
1. 下载并安装 [TWS](https://www.interactivebrokers.com/en/trading/tws.php) 或 [IB Gateway](https://www.interactivebrokers.com/en/trading/ibgateway-stable.php)
2. 登录 TWS/IB Gateway
3. 配置 API 权限：
   - 进入 `File` -> `Global Configuration` -> `API` -> `Settings`
   - 勾选 `Enable ActiveX and Socket Clients`
   - 设置 Socket Port: `7497` (TWS) 或 `4001` (IB Gateway)
   - 勾选 `Allow connections from localhost`
   - 取消勾选 `Read-Only API`
4. 确保在回测/实盘交易前 TWS/IB Gateway 已登录

---

## 3. 测试配置

### 测试 Telegram 连接
```bash
./trade/bin/python -c "
import os
from dotenv import load_dotenv
from src.notifications.telegram import send_telegram_message

load_dotenv('config/.env')

# 测试发送消息
send_telegram_message('🔔 Swing Trading Assistant 测试消息！\n\n配置成功！')
"
```

### 测试 IBKR 连接
```bash
./trade/bin/python -c "
import os
from dotenv import load_dotenv
from src.data.ibkr import IBKRPortfolio

load_dotenv('config/.env')

# 测试连接
ibkr = IBKRPortfolio()
positions = ibkr.get_positions()
print(f'当前持仓数量: {len(positions)}')
"
```

---

## 4. 安全注意事项

⚠️ **重要安全提示：**

1. **不要提交 `.env` 文件到 Git**
   - `.env` 已在 `.gitignore` 中
   - 只提交 `.env.example` 作为模板

2. **保护你的 API Keys**
   - 不要分享 `.env` 文件
   - 定期更换敏感的 API Keys
   - 为不同的环境使用不同的 Keys

3. **限制 API 权限**
   - 只授予必要的权限
   - 为生产环境使用只读权限（如适用）

---

## 5. 配置文件说明

### `config/config.yaml`
```yaml
# 交易策略配置
strategy:
  breakout:
    rsi_min: 60
    rsi_max: 75
    volume_multiplier: 1.5
  
  pullback:
    rsi_oversold: 30
    rsi_recovery_threshold: 0.5
  
  position:
    size: 0.10  # 每次交易使用 10% 资金
    risk_per_trade: 0.02  # 每次交易风险 2%

# 市场环境
market:
  vix_threshold: 30.0  # VIX > 30 时暂停交易

# 止损止盈
risk_management:
  stop_loss_pct: 5.0
  take_profit_pct: 10.0

# 股票池
stocks:
  us:
    - AAPL
    - MSFT
    - GOOGL
    # ... 更多美股
  
  my:
    - MAYBANK
    - CIMB
    # ... 更多马股
```

### `config/malaysia_ticker_mapping.json`
此文件包含马来西亚股票的映射关系（如 KLSE 代码到 Yahoo Finance 代码）。

---

## 6. 常见问题

### Q: Telegram 消息发送失败？
A: 检查：
1. `TELEGRAM_BOT_TOKEN` 是否正确
2. `TELEGRAM_CHAT_ID` 是否正确
3. 确保你已启动机器人（发送 `/start` 给你的机器人）

### Q: IBKR 连接失败？
A: 检查：
1. TWS/IB Gateway 是否正在运行
2. 是否已登录
3. API 设置是否正确
4. 防火墙是否允许连接

### Q: 数据下载失败？
A: 检查：
1. 网络连接是否正常
2. API 是否有调用限制
3. 股票代码是否正确

---

## 7. 首次运行检查清单

- [ ] 创建并配置 `config/.env` 文件
- [ ] 获取 Telegram Bot Token 和 Chat ID
- [ ] 测试 Telegram 消息发送
- [ ] 配置 IBKR 连接（如需实盘交易）
- [ ] 测试数据获取功能
- [ ] 运行快速回测：`./trade/bin/python test_backtest.py`
- [ ] 测试完整系统：`./trade/bin/python test_full_system.py`

---

## 8. 环境变量优先级

环境变量的加载顺序（后面的会覆盖前面的）：

1. 默认值（在代码中硬编码）
2. `config/.env` 文件
3. 系统环境变量（`export VAR=value`）

---

## 9. 查看当前配置

```bash
# 查看当前加载的环境变量
./trade/bin/python -c "
from dotenv import load_dotenv
import os

load_dotenv('config/.env')

print('当前配置：')
for key in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'IBKR_HOST', 'IBKR_PORT']:
    value = os.getenv(key)
    if value:
        # 隐藏敏感信息
        if 'TOKEN' in key or 'KEY' in key or 'ID' in key:
            print(f'{key}=***')
        else:
            print(f'{key}={value}')
"
```

---

## 需要帮助？

如果遇到配置问题，请查看：
- `TROUBLESHOOTING.md` - 故障排查指南
- `QUICKSTART.md` - 快速开始指南
- `README.md` - 项目文档