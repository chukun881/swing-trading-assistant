# 🚀 快速开始指南

## 📋 前置检查

- [ ] Python 3.8+ 已安装
- [ ] pip 已安装
- [ ] Git 已安装（可选）
- [ ] Telegram Bot Token 和 Chat ID（已配置）
- [ ] Interactive Brokers 账户（可选，用于持仓跟踪）

## 🎯 5 分钟快速启动

### 步骤 1: 安装依赖

```bash
# 进入项目目录
cd swing-trading-assistant

# 安装 Python 依赖
pip install -r requirements.txt
```

**如果 ta-lib 安装失败，请参考 README.md 中的详细安装步骤。**

### 步骤 2: 验证配置

```bash
# 检查配置文件是否存在
ls config/.env
ls config/config.yaml
```

**您的配置已经预先设置好了：**
- ✅ Telegram Bot Token: `8241159404:AAEe5-7dLVTXxPxtd1BKYfdBjxK6-M_Olqs`
- ✅ Telegram Chat ID: `902084713`
- ✅ IB Port: `7496`

### 步骤 3: (可选) 配置 Interactive Brokers

如果您想使用持仓跟踪功能：

1. 启动 **TWS (Trader Workstation)**
2. 进入 `File → Global Configuration`
3. 选择 `API → Settings`
4. 勾选 `Enable ActiveX and Socket Clients`
5. 设置 `Socket Port` 为 `7496`
6. 保存并重启 TWS

**如果不使用 IB 功能，可以跳过此步骤。程序仍然可以正常扫描市场并发送 Telegram 通知。**

### 步骤 4: 运行程序

```bash
python src/main.py
```

### 步骤 5: 查看 Telegram 通知

程序启动后，您应该在 Telegram 收到类似以下消息：

```
✅ Swing Trading Assistant started successfully!

📊 Market Scan Report

📈 Stocks Scanned: 30
🎯 Signals Found: 0
⏱️ Duration: 45.23 seconds

📋 No trading signals at this time.

✅ Market scan completed successfully!
```

## 📊 查看日志

```bash
# 查看今天的日志
tail -f logs/trading_assistant_$(date +%Y%m%d).log

# 或在另一个终端实时查看
tail -f logs/trading_assistant_*.log
```

## 🔧 调整策略参数

编辑 `config/config.yaml` 文件：

```bash
# 使用您喜欢的编辑器
nano config/config.yaml
# 或
vim config/config.yaml
# 或
code config/config.yaml
```

常用调整：
- 修改 RSI 阈值
- 调整止损/止盈百分比
- 改变扫描的股票数量

## 📱 测试 Telegram 通知

如果您想测试 Telegram 通知是否正常工作：

```bash
# Python 交互式测试
python3

>>> from src.notifications.telegram import create_telegram_notifier
>>> from dotenv import load_dotenv
>>> import os
>>> load_dotenv('config/.env')
>>> config = {
...     'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
...     'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID')
... }
>>> notifier = create_telegram_notifier(config)
>>> notifier.send_success("Test message - everything is working!")
```

## 🐛 常见问题速查

### 问题: 找不到模块
```bash
# 解决方案：确保在项目根目录运行
cd /path/to/swing-trading-assistant
python src/main.py
```

### 问题: Telegram 没有收到消息
```bash
# 检查日志
cat logs/trading_assistant_*.log | grep -i error

# 验证 .env 文件
cat config/.env
```

### 问题: IB 连接失败
```
这是正常的，如果：
- TWS 没有运行
- 端口配置不正确
- 市场关闭时间

程序会继续运行，只是不会获取持仓信息。
```

## 📝 下一步

1. **查看日志**: 了解程序运行情况
2. **调整参数**: 根据您的需求优化策略
3. **定期运行**: 每天手动运行一次（或设置定时任务）
4. **监控信号**: 关注 Telegram 通知

## 🎓 深入了解

- 阅读完整文档: `README.md`
- 查看策略逻辑: `src/analysis/` 目录
- 自定义配置: `config/config.yaml`
- 查看历史日志: `logs/` 目录

## 💡 提示

- 建议在市场开放时间运行（上午9:30 - 下午4:00 EST）
- 首次运行可能需要 1-2 分钟下载和计算数据
- 如果没有检测到信号是正常的，市场条件可能不符合
- 可以调整 `config.yaml` 中的参数使其更敏感

---

**需要帮助？** 查看 `README.md` 中的故障排除部分。