# Swing Trading Assistant - 部署指南

## 📋 概述

本系统已成功实现并测试所有核心功能：
- ✅ 获取 300+ 真实 Bursa Malaysia 股票（无 OTC 股票）
- ✅ 批量 yfinance 下载优化
- ✅ 智能代码转换（字母 → 数字）
- ✅ Breakout / Pullback 信号检测
- ✅ Portfolio tracking（使用 ibsync）
- ✅ Telegram 推送通知
- ✅ 零 404 错误和 Event loop 错误

## 🔑 API Keys 配置

### 1. 创建 `.env` 文件

在 `config/` 目录下创建 `.env` 文件：

```bash
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=你的_telegram_bot_token
TELEGRAM_CHAT_ID=你的_telegram_chat_id

# Interactive Brokers 配置（可选）
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1
```

### 2. 获取 Telegram Bot Token

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 命令
3. 按照提示创建机器人
4. 复制获得的 Token 并填入 `TELEGRAM_BOT_TOKEN`

### 3. 获取 Telegram Chat ID

**方法一（推荐）：**
1. 在 Telegram 中搜索 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息
3. 复制获得的 ID 并填入 `TELEGRAM_CHAT_ID`

**方法二：**
1. 向你的机器人发送任意消息
2. 访问：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. 查找 `"chat":{"id":数字}` 并复制该数字

### 4. Interactive Brokers 配置（可选）

如果不需要 portfolio tracking，可以留空这些值。

**TWS 配置：**
1. 打开 Interactive Brokers Trader Workstation (TWS)
2. 进入 `File` → `Global Configuration`
3. 找到 `API` → `Settings`
4. 勾选 `Enable ActiveX and Socket Clients`
5. 取消勾选 `Read-Only API`
6. 设置 Socket Port 为 `7497`（模拟账户）或 `7496`（真实账户）
7. 在 `Trusted IPs` 中添加 `127.0.0.1`

**IB Gateway 配置：**
1. 下载并安装 IB Gateway
2. 启动并登录
3. 在配置中启用 API
4. 设置端口为 `7497` 或 `7496`

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp config/.env.example config/.env
# 编辑 config/.env 文件，填入你的 API keys
```

### 3. 测试运行

```bash
# 测试完整系统
python3 test_full_system.py

# 测试 Malaysia API
python3 test_malaysia_api_final.py

# 运行主程序
python3 -m src.main
```

### 4. 设置每日自动运行

**使用 cron（Linux/macOS）：**

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天早上 9:00 运行）
0 9 * * * cd /path/to/swing-trading-assistant && python3 -m src.main >> logs/cron.log 2>&1
```

**使用 Windows 任务计划程序：**

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（每日）
4. 设置操作：启动程序
   - 程序：`python.exe`
   - 参数：`-m src.main`
   - 起始于：`C:\path\to\swing-trading-assistant`

## 📊 系统架构

```
Swing Trading Assistant
├── TradingView API
│   ├── US Market (NASDAQ, NYSE, AMEX)
│   └── Malaysia Market (MYX/Bursa)
├── Yahoo Finance
│   ├── 批量下载历史数据
│   └── OHLCV 数据
├── 技术分析
│   ├── EMA (20, 50)
│   ├── RSI (14)
│   ├── Bollinger Bands
│   ├── Pullback 检测
│   └── Breakout 检测
├── 信号生成
│   ├── BUY (Pullback/Breakout)
│   ├── SELL (技术性卖出)
│   ├── STOP LOSS (5%)
│   └── TAKE PROFIT (RSI > 75)
└── 通知系统
    └── Telegram 推送
```

## 📈 信号说明

### 买入信号（BUY）

**Pullback 策略：**
- RSI 从超卖区域（<30）回升
- 价格接近 EMA20 支撑
- 成交量确认

**Breakout 策略：**
- 价格突破布林带上轨
- RSI 在 60-75 之间
- 可能的 band squeeze

### 卖出信号（SELL）

- 价格跌破 EMA20
- RSI > 75（超买）
- 止损触发（-5%）
- 止盈触发（RSI > 75）

## 🔧 配置选项

编辑 `config/config.yaml`：

```yaml
# 技术指标参数
indicators:
  ema_short: 20
  ema_long: 50
  rsi_period: 14
  bollinger_period: 20
  bollinger_std: 2

# Pullback 参数
pullback:
  rsi_oversold: 30
  rsi_recovery_threshold: 0.5

# Breakout 参数
breakout:
  rsi_min: 60
  rsi_max: 75
  check_band_squeeze: true
  band_squeeze_threshold: 0.7

# Exit 策略
exit:
  stop_loss_pct: 0.05  # 5% 止损
  take_profit_rsi: 75
  trailing_stop_enabled: false

# 股票扫描配置
max_stocks_per_market: 300  # 每个市场最多扫描 300 只股票
```

## 📝 日志文件

日志保存在 `logs/` 目录：
- 文件名格式：`trading_assistant_YYYYMMDD.log`
- 包含详细的运行日志和错误信息

## ⚠️ 注意事项

1. **API 限制：**
   - TradingView API 无需 key，但有速率限制
   - Yahoo Finance 免费，建议每日运行 1-2 次
   - Telegram Bot 每天最多发送 30 条消息

2. **股票代码映射：**
   - 系统已预定义 75+ 个马来西亚股票映射
   - 如需添加更多，编辑 `src/data/ticker_converter.py`
   - 或手动添加到 `config/malaysia_ticker_mapping.json`

3. **性能优化：**
   - 使用批量下载（yf.download）而非单个请求
   - 每个市场最多处理 300 只股票
   - 智能过滤不可转换的股票

4. **风险提示：**
   - 本系统仅供参考，不构成投资建议
   - 投资有风险，决策需谨慎
   - 建议结合其他分析方法

## 🐛 故障排除

### 问题：Telegram 通知未收到

**解决方案：**
1. 检查 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 是否正确
2. 确保 Bot 已启动并添加到联系人
3. 测试连接：
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

### 问题：无法连接 IBKR

**解决方案：**
1. 确保 TWS/IB Gateway 正在运行
2. 检查 API 是否已启用
3. 验证端口配置（7497 或 7496）
4. 检查防火墙设置

### 问题：马来西亚股票数据缺失

**解决方案：**
1. 检查股票代码映射
2. 添加到预定义映射表
3. 某些股票可能在 Yahoo Finance 上不可用

## 📞 支持

如有问题，请检查：
1. `logs/` 目录下的日志文件
2. GitHub Issues
3. 系统测试：`python3 test_full_system.py`

## 🎯 下一步

- [ ] 添加更多马来西亚股票映射
- [ ] 实现回测功能
- [ ] 添加更多技术指标
- [ ] 支持更多市场（新加坡、香港等）
- [ ] 添加机器学习预测
- [ ] 创建 Web Dashboard

---

**最后更新：** 2026-04-23  
**版本：** 1.0.0