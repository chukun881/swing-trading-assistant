# Swing Trading Assistant

基于技术指标的 Swing Trading 交易助手，支持美国市场扫描和回测。

## 功能特性

- ✅ **市场扫描**: 扫描 Russell 1000 股票，寻找交易机会
- ✅ **技术分析**: 使用 RSI, EMA, MACD, VIX 等指标
- ✅ **信号生成**: 自动生成 BUY / HOLD / SELL 建议
- ✅ **回测引擎**: 基于 Backtrader 的完整回测系统
- ✅ **Telegram 推送**: 实时发送交易信号到 Telegram

## 架构设计

```
src/
├── analysis/
│   └── breakout.py      # 策略大脑 - 所有指标计算和信号生成
├── backtest_engine.py   # 回测引擎 - 执行交易和管理仓位
├── main.py              # 实时扫描器 - 数据获取和 Telegram 通知
└── notifications/
    └── telegram.py      # Telegram 通知模块
```

**核心架构原则**:
- `src/analysis/breakout.py`: 唯一的策略"大脑"
- `src/backtest_engine.py`: "愚蠢"引擎，只执行交易
- `src/main.py`: 实时扫描器，负责数据获取和通知

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv trade
source trade/bin/activate  # Linux/Mac
# 或
trade\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env` 并填入你的 Telegram 配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**如何获取 Telegram 配置**:

1. 在 Telegram 中找到 @BotFather
2. 发送 `/newbot` 创建新机器人
3. 复制 Bot Token 填入 `TELEGRAM_BOT_TOKEN`
4. 给你的机器人发送一条消息
5. 访问 `https://api.telegram.org/bot<your_token>/getUpdates`
6. 找到 `chat":{"id":123456789}` 中的数字填入 `TELEGRAM_CHAT_ID`

### 3. 运行回测

```bash
python test_backtest.py
```

回测结果示例：
```
============================================================
BACKTEST RESULTS
============================================================
Initial Capital: $10,000.00
Final Portfolio Value: $13,224.84
Total Return: +32.25%
Total Trades: 1457
Winning Trades: 499
Losing Trades: 958
Win Rate: 34.25%
Maximum Drawdown: 25.72%
============================================================
```

### 4. 运行实时扫描

```bash
python src/main.py
```

扫描完成后会收到 Telegram 通知：
```
🔥 BUY 信号

📈 AAPL
💰 价格: $173.50
📊 RSI: 72.3
📅 日期: 2026-04-22
```

### 5. 设置定时任务（每日自动运行）

**Linux/Mac (cron)**:
```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天 9:30 运行，美股开盘前）
30 9 * * 1-5 cd /path/to/swing-trading-assistant && /path/to/trade/bin/python src/main.py >> logs/cron.log 2>&1
```

**Windows (Task Scheduler)**:
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置每天 9:30 AM 运行
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`src/main.py`
   - 起始于：`C:\path\to\swing-trading-assistant`

## 交易策略

### 买入条件

1. **价格突破**: 收盘价 > EMA(50)
2. **动量确认**: MACD 柱状图 > 0
3. **趋势过滤**: EMA(20) > EMA(50)
4. **强度过滤**: RSI > 50
5. **市场环境**: SPY > EMA(200) 且 VIX < 30

### 卖出条件

1. **移动止损**: 价格跌破 EMA(20)
2. **硬止损**: 价格跌破入场价 -5%

## 配置选项

### 修改策略参数

编辑 `src/analysis/breakout.py`:

```python
# 买入条件
RSI_BUY_THRESHOLD = 50       # RSI 买入阈值
VIX_MAX = 30                 # VIX 最大值

# 指标参数
EMA_FAST = 20                # 快速 EMA
EMA_SLOW = 50                # 慢速 EMA
EMA_TREND = 200              # 趋势 EMA

# 止损
HARD_STOP_LOSS = 0.05        # 硬止损 -5%
```

### 修改扫描配置

编辑 `src/main.py`:

```python
# 扫描配置
max_signals = 5              # 最大返回信号数
days = 365                   # 历史数据天数
```

## 测试新架构

快速测试新架构（只测试 5 只股票）：

```bash
python test_architecture.py
```

## 日志文件

- `logs/scanner_YYYYMMDD.log`: 实时扫描日志
- `backtest_trades.csv`: 回测交易记录

## 故障排查

### Telegram 消息收不到

1. 检查 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 是否正确
2. 确保你已经给机器人发送过消息
3. 检查网络连接

### 回测没有交易

1. 检查数据是否有足够的长度（至少 50 天）
2. 查看日志中的信号统计
3. 尝试调整策略参数

### 扫描速度慢

1. 减少扫描的股票数量
2. 使用缓存的数据文件

## 免责声明

⚠️ **重要提示**:

- 本项目仅供学习和研究使用
- 不构成任何投资建议
- 过往表现不代表未来收益
- 实盘交易有风险，请谨慎操作
- 使用本项目产生的任何损失，作者不承担责任

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！