# 📈 Swing Trading Assistant

一个基于技术分析的智能摆动交易助手，专注于美国股票市场（Russell 1000），自动扫描和信号检测。

## ✨ 功能特性

- 🇺🇸 **美国市场**: 专注于 Russell 1000 大盘股 (NASDAQ, NYSE, AMEX)
- 📊 **技术分析**: EMA, RSI, Bollinger Bands 等技术指标
- 🎯 **智能信号**: 自动检测 Pullback 和 Breakout 买入信号
- 💰 **持仓管理**: 自动监控持仓的退出信号 (止损/止盈/卖出)
- 📱 **Telegram通知**: 实时推送交易信号和账户状态
- 🔧 **灵活配置**: 可调整所有策略参数
- 📝 **日志记录**: 完整的操作日志便于追踪和调试
- 🛡️ **市场过滤**: 基于 VIX 指数过滤高风险环境

## 🎯 交易策略

### Pullback 策略
**买入条件:**
- ✅ Price > EMA50
- ✅ EMA20 > EMA50
- ✅ Price 触碰下轨 (≤ BB Lower)
- ✅ RSI < 30 且开始回升
- ✅ 出现看涨K线形态（锤子线/十字星/吞没阳线）

**动作:** BUY

### Breakout 策略
**买入条件:**
- ✅ Price > EMA50
- ✅ Close > 上轨 (BB Upper)
- ✅ RSI 在 60-75 范围内
- ✅ 成交量 > 20日平均成交量 × 1.5

**动作:** BUY 或 WAIT RETEST

### Exit 策略
**卖出条件:**
- 🚨 Price < EMA20 → SELL
- 💰 RSI > 75 → TAKE PROFIT
- 🛑 亏损超过 5% → STOP LOSS
- 📈 盈利超过 10% → TAKE PROFIT

### 市场过滤
- ⚠️ VIX > 30 → 暂停新买入信号
- ✅ VIX ≤ 30 → 正常交易

## 📦 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/chukun881/swing-trading-assistant.git
cd swing-trading-assistant
```

### 2. 创建虚拟环境
```bash
python3 -m venv trade
source trade/bin/activate  # Linux/Mac
# 或
trade\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

## ⚙️ 配置说明

### 🔑 API Key 配置

**所有敏感信息都放在 `config/.env` 文件中，此文件已加入 `.gitignore` 不会被提交到 Git。**

#### 1. 创建/编辑 `config/.env` 文件

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Interactive Brokers TWS Configuration (可选，用于实盘交易)
IB_HOST=127.0.0.1
IB_PORT=7497  # TWS: 7497, IB Gateway: 4001
IB_CLIENT_ID=1
```

**详细配置步骤请查看 [CONFIG_GUIDE.md](CONFIG_GUIDE.md)**

#### 2. 获取 Telegram Bot Token
1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按照提示设置机器人名称和用户名
4. BotFather 会返回一个 API Token
5. 将 Token 复制到 `.env` 文件的 `TELEGRAM_BOT_TOKEN`

#### 3. 获取 Telegram Chat ID
1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息给这个机器人
3. 它会返回你的 Chat ID
4. 将 Chat ID 复制到 `.env` 文件的 `TELEGRAM_CHAT_ID`

#### 4. IBKR 配置（可选）
1. 下载并安装 [TWS](https://www.interactivebrokers.com/en/trading/tws.php)
2. 登录 TWS
3. 配置 API 权限：
   - 进入 `File` -> `Global Configuration` -> `API` -> `Settings`
   - 勾选 `Enable ActiveX and Socket Clients`
   - 设置 Socket Port: `7497`
   - 勾选 `Allow connections from localhost`

### 📝 策略参数配置

编辑 `config/config.yaml` 文件来自定义策略参数：

```yaml
# 技术指标参数
indicators:
  ema_short: 20
  ema_long: 50
  rsi_period: 14
  bollinger_period: 20
  bollinger_std: 2

# Pullback策略参数
pullback:
  rsi_oversold: 30
  rsi_recovery_threshold: 0.5

# Breakout策略参数
breakout:
  rsi_min: 60
  rsi_max: 75
  check_band_squeeze: true
  band_squeeze_threshold: 0.7

# Exit策略参数
exit:
  stop_loss_pct: 0.05  # 5%止损
  take_profit_rsi: 75
  trailing_stop_enabled: false

# 市场配置（仅美国市场）
markets:
  us:
    exchanges: ["NASDAQ", "NYSE", "AMEX"]
    min_volume: 1000000

# VIX 市场过滤器
market_filter:
  vix_threshold: 30.0  # VIX > 30 时暂停交易
```

## 🚀 使用方法

### 1. 运行回测

```bash
# 快速测试（3年数据，50只股票）
./trade/bin/python test_backtest.py

# 完整回测
./trade/bin/python src/backtest_engine.py
```

### 2. 运行主程序

```bash
./trade/bin/python src/main.py
```

程序会：
1. 连接 Telegram Bot
2. 连接 Interactive Brokers（如果 TWS 正在运行）
3. 扫描美国股票市场（Russell 1000）
4. 检测交易信号
5. 检查持仓的退出信号
6. 发送 Telegram 通知

### 3. 设置定时任务

```bash
crontab -e

# 每天上午 9 点运行（美国市场开盘前）
0 9 * * * cd /Users/chukun881/Code/swing-trading-assistant && ./trade/bin/python src/main.py >> logs/daily_run.log 2>&1

# 或者在市场收盘后运行
30 16 * * * cd /Users/chukun881/Code/swing-trading-assistant && ./trade/bin/python src/main.py >> logs/daily_run.log 2>&1
```

### 4. 查看日志

运行日志保存在 `logs/` 目录：
```
logs/trading_assistant_20260423.log
```

## 📁 项目结构

```
swing-trading-assistant/
├── config/
│   ├── .env                  # 🔑 敏感信息（API Keys等）
│   ├── .env.example          # 环境变量模板
│   └── config.yaml           # 策略参数配置
├── src/
│   ├── analysis/
│   │   ├── indicators.py     # 技术指标计算
│   │   ├── pullback.py       # Pullback 策略
│   │   ├── breakout.py       # Breakout 策略
│   │   └── signals.py        # 信号生成
│   ├── data/
│   │   ├── tradingview.py    # TradingView 数据获取
│   │   └── ibkr.py          # IB 连接和持仓管理
│   ├── notifications/
│   │   └── telegram.py      # Telegram 通知
│   ├── backtest_engine.py    # 回测引擎
│   └── main.py              # 主程序
├── test_*.py                 # 测试脚本
├── logs/                     # 运行日志
├── requirements.txt          # Python 依赖
├── README.md                 # 项目文档
├── CONFIG_GUIDE.md           # 配置指南
├── PROJECT_SUMMARY.md        # 项目总结
├── QUICKSTART.md             # 快速开始
└── .gitignore
```

## 📊 Telegram 通知示例

程序会发送以下类型的 Telegram 通知：

### 买入信号
```
📈 BREAKOUT Signal: BUY

📌 Symbol: AAPL
💰 Price: $150.50
🎯 Confidence: HIGH

📊 Analysis:
Breakout detected at $150.50
• Price > EMA50: True
• Price > BB Upper: True
• RSI (68.5) in range [60, 75]
• Volume: 1.8x average
```

### 退出信号
```
🔴 STOP LOSS Signal

📌 Symbol: AAPL
💰 Current Price: $142.50
📥 Entry Price: $150.00
📊 PnL: -5.00% ($-7.50)

📊 Analysis:
Stop Loss triggered at $142.50
• Entry: $150.00
• PnL: -5.00% (Limit: -5.0%)
```

### 每日报告
```
📊 Swing Trading Assistant - 每日报告

📅 日期: 2026-04-23

🔍 Breakout 信号:
📈 AAPL - BUY
   价格: $276.23
   RSI: 68.1
   成交量倍数: 1.8x

🔄 Pullback 信号:
📈 GOOGL - BUY
   价格: $138.45
   RSI: 28.5
   形态: Hammer

💼 当前持仓:
- AAPL: 3股 @ $276.23 (-5.25%)

⚠️ 风险提示:
- VIX: 25.3 (市场正常)
- 建议仓位: 10%
```

## ⚠️ 重要注意事项

1. **TWS 连接（可选）:**
   - IB API 在市场关闭时可能限制数据访问
   - 确保 TWS 正在运行且已登录
   - 确保 API 权限已正确配置

2. **数据源限制:**
   - TradingView 免费库可能有请求频率限制
   - yfinance 数据可能有延迟
   - 建议在市场开放时间运行

3. **风险管理:**
   - ⚠️ 这只是辅助工具，不构成投资建议
   - 请根据自己的风险承受能力调整参数
   - 建议先在模拟账户测试
   - 永远不要投入超过你能承受损失的资金

4. **性能优化:**
   - 当前默认扫描 300 只股票
   - 可在 `config/config.yaml` 中调整 `max_stocks`
   - 扫描更多股票会增加运行时间

5. **网络连接:**
   - 需要稳定的互联网连接
   - 数据获取失败会记录在日志中

## 🐛 故障排除

### 问题 1: 无法连接到 IB TWS
**解决方案:**
- 确保 TWS 正在运行
- 检查 API 端口是否为 7497
- 确认 API 权限已启用
- 检查防火墙设置

### 问题 2: Telegram 通知未收到
**解决方案:**
- 检查 `config/.env` 中的 Token 和 Chat ID
- 确认网络连接正常
- 查看日志中的错误信息

### 问题 3: 没有检测到信号
**解决方案:**
- 检查市场是否开放
- 调整策略参数（如 RSI 阈值）
- 增加扫描的股票数量
- 查看日志了解详细信息
- 检查 VIX 是否超过阈值

### 问题 4: 回测失败
**解决方案:**
- 检查网络连接
- 查看是否有数据下载错误
- 尝试减少测试股票数量
- 查看日志中的详细错误信息

## 📈 性能指标

- **扫描速度**: ~50-100 只股票/分钟
- **回测范围**: 3年历史数据
- **信号准确性**: 取决于市场条件和参数设置
- **资源占用**: 低（CPU 和内存占用很少）

## 📚 相关文档

- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - 详细的配置指南
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - 项目总结
- **[QUICKSTART.md](QUICKSTART.md)** - 快速开始指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [tradingview-screener](https://github.com/nqt101/tradingview-screener) - TradingView 数据获取
- [ib_insync](https://github.com/erdewit/ib_insync) - Interactive Brokers API
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance 数据
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API
- [backtrader](https://github.com/mementum/backtrader) - 回测框架

---

**⚠️ 免责声明:** 本软件仅供教育和研究目的。使用本软件进行交易的所有风险由用户自行承担。作者不对任何交易损失负责。请在进行实际交易前充分测试并咨询专业金融顾问。

**📧 联系方式:** 如有问题，请通过 GitHub Issues 联系。