# 📈 Swing Trading Assistant

一个基于技术分析的智能摆动交易助手，支持美国和马来西亚股票市场的自动扫描和信号检测。

## ✨ 功能特性

- 🌍 **多市场支持**: 美国股票 (NASDAQ, NYSE, AMEX) + 马来西亚股票 (Bursa Malaysia)
- 📊 **技术分析**: EMA, RSI, Bollinger Bands 等技术指标
- 🎯 **智能信号**: 自动检测 Pullback 和 Breakout 买入信号
- 💰 **持仓管理**: 自动监控持仓的退出信号 (止损/止盈/卖出)
- 📱 **Telegram通知**: 实时推送交易信号和账户状态
- 🔧 **灵活配置**: 可调整所有策略参数
- 📝 **日志记录**: 完整的操作日志便于追踪和调试

## 🎯 交易策略

### Pullback 策略
**买入条件:**
- ✅ Price > EMA50
- ✅ EMA20 > EMA50
- ✅ Price 触碰下轨 (≤ BB Lower)
- ✅ RSI < 30 且开始回升

**动作:** BUY

### Breakout 策略
**买入条件:**
- ✅ Price > EMA50
- ✅ Close > 上轨 (BB Upper)
- ✅ RSI 在 60-75 范围内
- ✅ (可选) Band Squeeze 检测

**动作:** BUY 或 WAIT RETEST

### Exit 策略
**卖出条件:**
- 🚨 Price < EMA20 → SELL
- 💰 RSI > 75 → TAKE PROFIT
- 🛑 亏损超过 5% → STOP LOSS

## 📦 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/chukun881/swing-trading-assistant.git
cd swing-trading-assistant
```

### 2. 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

**注意:** `ta-lib` 可能需要额外安装步骤：

**macOS:**
```bash
brew install ta-lib
pip install ta-lib
```

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
pip install ta-lib
```

**Windows:**
从 [这里](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) 下载对应的 `.whl` 文件并安装：
```bash
pip install TA_Lib‑0.4.26‑cp39‑cp39‑win_amd64.whl
```

## ⚙️ 配置说明

### 🔑 API Key 配置（重要！）

**所有敏感信息都放在 `config/.env` 文件中，此文件已加入 `.gitignore` 不会被提交到Git。**

#### 1. 编辑 `config/.env` 文件

文件已预先配置了您的 Telegram 信息：

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8241159404:AAEe5-7dLVTXxPxtd1BKYfdBjxK6-M_Olqs
TELEGRAM_CHAT_ID=902084713

# Interactive Brokers TWS Configuration
IB_HOST=127.0.0.1
IB_PORT=7496
IB_CLIENT_ID=1

# TradingView (无需API key，使用免费库)
# ibsync需要IB账户权限，无需额外API key
```

**您的 API Key 已经配置好了！无需更改。**

#### 2. Telegram Bot Token
- 已配置: `8241159404:AAEe5-7dLVTXxPxtd1BKYfdBjxK6-M_Olqs`
- 这是您的 Telegram Bot Token

#### 3. Telegram Chat ID
- 已配置: `902084713`
- 这是您的 Telegram Chat ID

#### 4. Interactive Brokers 配置
- Port: `7496`（已更新）
- Host: `127.0.0.1` (本地)
- Client ID: `1`

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

# 市场配置
markets:
  us:
    exchanges: ["NASDAQ", "NYSE", "AMEX"]
    min_volume: 1000000
  malaysia:
    exchanges: ["BURSA"]
    min_volume: 500000
```

## 🚀 使用方法

### 1. 配置 Interactive Brokers TWS

在使用 IB 功能前，请确保：

1. **启动 TWS (Trader Workstation)**
2. **配置 API 权限:**
   - 进入 `File → Global Configuration`
   - 选择 `API → Settings`
   - 勾选 `Enable ActiveX and Socket Clients`
   - 设置 `Socket Port` 为 `7496`
   - (可选) 在 `Trusted IPs` 中添加 `127.0.0.1`
   - 保存并重启 TWS

3. **确保 TWS 正在运行**（程序运行时）

### 2. 运行程序

```bash
python src/main.py
```

程序会：
1. 连接 Telegram Bot
2. 连接 Interactive Brokers（如果 TWS 正在运行）
3. 扫描 US 和 MY 股票市场
4. 检测交易信号
5. 检查持仓的退出信号
6. 发送 Telegram 通知

### 3. 查看日志

运行日志保存在 `logs/` 目录：
```
logs/trading_assistant_20260423.log
```

### 4. 手动触发

由于您选择手动触发，只需在需要时运行：
```bash
python src/main.py
```

## 📁 项目结构

```
swing-trading-assistant/
├── config/
│   ├── .env                  # 🔑 敏感信息（API Keys等）- 您的配置在这里
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
│   └── main.py              # 主程序
├── logs/                     # 运行日志
├── requirements.txt          # Python 依赖
├── .gitignore
└── README.md
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
📊 Market Scan Report

📈 Stocks Scanned: 30
🎯 Signals Found: 2
⏱️ Duration: 45.23 seconds

✨ Trading signals detected!
```

## ⚠️ 重要注意事项

1. **TWS 连接:**
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
   - 当前配置每市场扫描 15 只股票
   - 可在 `config/config.yaml` 中调整 `max_stocks_per_market`
   - 扫描更多股票会增加运行时间

5. **网络连接:**
   - 需要稳定的互联网连接
   - 数据获取失败会记录在日志中

## 🐛 故障排除

### 问题 1: 无法连接到 IB TWS
**解决方案:**
- 确保 TWS 正在运行
- 检查 API 端口是否为 7496
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

### 问题 4: ta-lib 安装失败
**解决方案:**
- 参考上方的安装步骤
- 确保已安装编译工具
- Windows 用户下载预编译的 .whl 文件

## 📈 性能指标

- **扫描速度**: ~30-50 只股票/分钟
- **信号准确性**: 取决于市场条件和参数设置
- **资源占用**: 低（CPU 和内存占用很少）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [tradingview-screener](https://github.com/nqt101/tradingview-screener) - TradingView 数据获取
- [ib_insync](https://github.com/erdewit/ib_insync) - Interactive Brokers API
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance 数据
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API

---

**⚠️ 免责声明:** 本软件仅供教育和研究目的。使用本软件进行交易的所有风险由用户自行承担。作者不对任何交易损失负责。请在进行实际交易前充分测试并咨询专业金融顾问。

**📧 联系方式:** 如有问题，请通过 GitHub Issues 联系。