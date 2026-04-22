# 🔧 故障排除指南

本文档记录了已知问题及其解决方案。

## ✅ 已修复的问题

### 1. IBKR Position Attribute Error

**问题描述:**
```
Error: 'Position' object has no attribute 'marketPrice'
```

**原因:**
在 `ib_insync` 库中，`Position` 对象只包含 `contract`、`position` 和 `avgCost` 属性，不包含 `marketPrice()` 方法。

**解决方案:**
- ✅ 已将 `ib.positions()` 更改为 `ib.portfolio()`
- ✅ `portfolio()` 返回的对象包含所有市场价值信息
- ✅ 修改了属性访问方式（从 `marketPrice()` 改为 `marketPrice`）

**修改文件:** `src/data/ibkr.py`

---

### 2. TradingView Screener API Error

**问题描述:**
```
Error: 'Column' object has no attribute 'eq'
```

**原因:**
`tradingview-screener` 库的 API 可能存在版本不兼容或使用方法不正确的问题。

**解决方案:**
- ✅ 更新了 Column 方法调用：
  - `.eq()` → `.equals()`
  - `.gte()` → `.greater_than()`
  - `.order_by()` → 添加 `order='desc'` 参数
- ✅ 添加了备用方案（Fallback）：
  - 当 TradingView Screener 失败时，自动使用预定义的热门股票列表
  - 美国：AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, JPM, V, JNJ
  - 马来西亚：MAYBANK, CIMB, PUBLICBANK, RHBBANK, TENAGA, MAXIM, IOICORP, SIME

**修改文件:** `src/data/tradingview.py`

**日志提示:**
如果看到 `Using fallback method for US/Malaysia stocks`，说明正在使用备用方案。

---

### 3. SSL/LibreSSL Warning (macOS)

**问题描述:**
```
NotOpenSSLWarning: The urllib3 package is insecure
```

**原因:**
macOS 系统默认使用 LibreSSL，而 Python 的某些库期望使用 OpenSSL。

**解决方案:**
- ✅ 在 `requirements.txt` 中添加了特定版本的 `urllib3` 和 `certifi`
- ✅ 确保使用兼容的 SSL 库版本

**修改文件:** `requirements.txt`

**额外步骤（如果问题仍然存在）:**

**方法 1: 更新 Python SSL（推荐）**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 重新安装依赖
pip install --upgrade urllib3 certifi
```

**方法 2: 使用 Homebrew 安装 OpenSSL（macOS）**
```bash
# 安装 OpenSSL
brew install openssl

# 设置环境变量
export LDFLAGS="-L/opt/homebrew/opt/openssl/lib"
export CPPFLAGS="-I/opt/homebrew/opt/openssl/include"
export PATH="/opt/homebrew/opt/openssl/bin:$PATH"

# 重新安装依赖
pip install --upgrade -r requirements.txt
```

**方法 3: 忽略警告（临时方案）**
```bash
# 在运行程序时设置环境变量
export PYTHONWARNINGS="ignore::urllib3.exceptions.NotOpenSSLWarning"
python src/main.py
```

---

## 🔍 常见问题排查

### 问题: 程序运行但没有检测到任何信号

**可能原因:**
1. 市场条件不符合策略条件
2. 策略参数过于严格
3. 数据获取失败

**排查步骤:**
```bash
# 1. 查看日志
cat logs/trading_assistant_*.log | grep -i "error"

# 2. 检查是否使用了备用方案
cat logs/trading_assistant_*.log | grep "fallback"

# 3. 查看扫描了多少只股票
cat logs/trading_assistant_*.log | grep "stocks retrieved"

# 4. 检查是否有数据
cat logs/trading_assistant_*.log | grep "Retrieved data for"
```

**解决方案:**
- 如果使用了 fallback，说明 TradingView Screener 不可用，但程序仍在运行
- 调整 `config/config.yaml` 中的策略参数，使其更宽松
- 增加 `max_stocks_per_market` 参数值
- 确保在市场开放时间运行

---

### 问题: Telegram 没有收到任何通知

**可能原因:**
1. Bot Token 或 Chat ID 错误
2. 网络连接问题
3. Telegram API 限制

**排查步骤:**
```bash
# 1. 验证配置
cat config/.env

# 2. 检查日志中的 Telegram 错误
cat logs/trading_assistant_*.log | grep -i "telegram"

# 3. 测试 Telegram 连接
python3 -c "
from src.notifications.telegram import create_telegram_notifier
from dotenv import load_dotenv
import os
load_dotenv('config/.env')
config = {
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
    'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID')
}
notifier = create_telegram_notifier(config)
if notifier:
    notifier.send_success('Test message')
else:
    print('Failed to initialize notifier')
"
```

---

### 问题: IB 连接失败

**可能原因:**
1. TWS 没有运行
2. API 端口配置错误
3. 市场关闭时间
4. 防火墙阻止

**排查步骤:**
```bash
# 1. 检查 TWS 是否运行（macOS）
ps aux | grep -i "trader workstation"

# 2. 检查端口是否在监听
lsof -i :7496

# 3. 查看日志中的 IB 错误
cat logs/trading_assistant_*.log | grep -i "ibkr\|tws"
```

**解决方案:**
- 确保 TWS 正在运行且已登录
- 检查 API 端口是否为 7496
- 确认 "Enable ActiveX and Socket Clients" 已勾选
- 尝试重启 TWS

**注意:** IB 连接失败不会影响主要功能（市场扫描和信号检测），只是无法获取持仓信息。

---

### 问题: ta-lib 安装失败

**常见错误:**
```
Command errored out with exit status 1: python setup.py egg_info
```

**解决方案:**

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
从 [LFD.uci.edu](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) 下载对应 Python 版本的 `.whl` 文件：
```bash
pip install TA_Lib‑0.4.26‑cp39‑cp39‑win_amd64.whl
```

---

## 📊 性能优化建议

### 1. 减少扫描时间

如果程序运行时间过长：

```yaml
# 在 config/config.yaml 中减少扫描数量
# 或者修改 src/main.py 中的 max_stocks_per_market 参数
```

### 2. 调整请求延迟

如果遇到 API 限制：

```python
# 在 src/data/tradingview.py 中调整延迟
time.sleep(0.5)  # 增加到 1.0 或 2.0
```

### 3. 使用缓存

考虑添加数据缓存功能以减少重复请求。

---

## 🆘 获取帮助

如果以上方法都无法解决问题：

1. **查看完整日志:**
   ```bash
   tail -100 logs/trading_assistant_$(date +%Y%m%d).log
   ```

2. **检查系统环境:**
   ```bash
   python --version
   pip --version
   pip list | grep -E "tradingview|ib_insync|yfinance|ta-lib"
   ```

3. **提交 Issue:**
   - 提供错误日志
   - 说明操作系统和 Python 版本
   - 描述复现步骤

---

## 📝 更新日志

### 2026-04-23
- ✅ 修复 IBKR Position attribute error
- ✅ 修复 TradingView Screener API error
- ✅ 添加 TradingView 数据获取的备用方案
- ✅ 修复 SSL/LibreSSL 警告
- ✅ 更新依赖版本

---

**最后更新:** 2026-04-23