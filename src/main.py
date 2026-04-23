"""
Swing Trading Assistant - 实时市场扫描器

职责：
- 获取 US 股票数据
- 使用 breakout.py（大脑）计算指标和信号
- 输出 BUY / HOLD / SELL 建议
- 通过 Telegram 推送

架构：
- src/analysis/breakout.py: 唯一的策略大脑
- 此文件: 数据获取 + Telegram 通知
"""
import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import yfinance as yf

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analysis.breakout import add_signals_to_dataframe, calculate_indicators_batch
from src.notifications.telegram import TelegramNotifier

# ============================================================================
# 配置和日志
# ============================================================================

def setup_logging():
    """配置日志"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'scanner_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()

# ============================================================================
# 股票列表
# ============================================================================

RUSSELL_1000_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'BRK.B', 'LLY', 'AVGO',
    'TSLA', 'JPM', 'XOM', 'V', 'UNH', 'MA', 'JNJ', 'PG', 'COST', 'HD',
    'MRK', 'ABBV', 'CVX', 'BAC', 'KO', 'PEP', 'WMT', 'AMD', 'NFLX', 'CSCO',
    'ADBE', 'CRM', 'QCOM', 'WFC', 'ABT', 'PFE', 'ORCL', 'INTC', 'DIS', 'VZ',
    'TMO', 'DHR', 'NKE', 'MCD', 'IBM', 'ACN', 'GE', 'TXN', 'LLY', 'D',
    # 添加更多 Russell 1000 股票...
]

def get_russell_1000() -> List[str]:
    """
    获取 Russell 1000 股票列表
    
    返回: 股票代码列表
    """
    # 尝试从维基百科获取
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = "https://en.wikipedia.org/wiki/Russell_1000_Index"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到包含股票列表的表格
        table = soup.find('table', {'class': 'wikitable sortable'})
        if table:
            tickers = []
            for row in table.find_all('tr')[1:]:  # 跳过表头
                cells = row.find_all('td')
                if cells:
                    ticker = cells[0].text.strip().replace('.', '-')
                    if ticker and ticker not in ['Date', 'Ticker']:
                        tickers.append(ticker)
            
            if len(tickers) > 100:  # 确保获取到合理数量
                logger.info(f"从维基百科获取了 {len(tickers)} 只 Russell 1000 股票")
                return tickers
    except Exception as e:
        logger.warning(f"从维基百科获取股票列表失败: {e}")
    
    # 回退到硬编码列表
    logger.info("使用硬编码的股票列表")
    return RUSSELL_1000_TICKERS


# ============================================================================
# 数据获取
# ============================================================================

def download_stock_data(tickers: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
    """
    下载股票数据
    
    Args:
        tickers: 股票代码列表
        days: 历史天数
        
    Returns:
        {ticker: DataFrame} 字典
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    logger.info(f"下载 {len(tickers)} 只股票的数据 ({start_date} 到 {end_date})")
    
    data_dict = {}
    
    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                continue
            
            # 处理 MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 标准化列名
            df.index = pd.to_datetime(df.index)
            df.columns = [str(col).lower() for col in df.columns]
            
            data_dict[ticker] = df
            
            if (i + 1) % 50 == 0:
                logger.info(f"已下载 {i + 1}/{len(tickers)} 只股票")
                
        except Exception as e:
            logger.debug(f"下载 {ticker} 失败: {e}")
            continue
    
    logger.info(f"成功下载 {len(data_dict)} 只股票的数据")
    return data_dict


def download_market_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    下载市场数据 (SPY 和 VIX)
    
    Returns:
        (spy_df, vix_df)
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    logger.info("下载市场数据 (SPY 和 VIX)...")
    
    spy_df = yf.download('SPY', start=start_date, end=end_date, progress=False)
    vix_df = yf.download('^VIX', start=start_date, end=end_date, progress=False)
    
    # 标准化
    for df in [spy_df, vix_df]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        df.columns = [str(col).lower() for col in df.columns]
    
    return spy_df, vix_df


# ============================================================================
# 信号扫描
# ============================================================================

def scan_market(tickers: List[str], max_signals: int = 5) -> List[Dict]:
    """
    扫描市场寻找交易信号
    
    Args:
        tickers: 股票代码列表
        max_signals: 最大返回信号数
        
    Returns:
        信号列表
    """
    logger.info("=" * 60)
    logger.info("开始市场扫描")
    logger.info("=" * 60)
    start_time = time.time()
    
    # 下载市场数据
    spy_df, vix_df = download_market_data()
    
    # 下载股票数据
    stock_data = download_stock_data(tickers)
    
    if not stock_data:
        logger.error("没有下载到任何股票数据")
        return []
    
    # 计算指标和信号（使用 breakout.py）
    logger.info("计算技术指标和信号...")
    stock_data = calculate_indicators_batch(stock_data, spy_df, vix_df)
    
    # 分析信号
    buy_signals = []
    hold_signals = []
    sell_signals = []
    
    for ticker, df in stock_data.items():
        if len(df) < 50:  # 需要足够的数据
            continue
        
        # 获取最新数据
        latest = df.iloc[-1]
        
        # 检查信号
        if latest['Buy_Signal'] == 1:
            buy_signals.append({
                'ticker': ticker,
                'price': latest['close'],
                'rsi': latest['rsi'],
                'volume': latest['volume'],
                'date': df.index[-1],
            })
        elif latest['Sell_Signal'] == 1:
            sell_signals.append({
                'ticker': ticker,
                'price': latest['close'],
                'rsi': latest['rsi'],
                'date': df.index[-1],
            })
        else:
            hold_signals.append({
                'ticker': ticker,
                'price': latest['close'],
                'rsi': latest['rsi'],
                'date': df.index[-1],
            })
    
    # 按 RSI 排序 BUY 信号（高 RSI 优先）
    buy_signals.sort(key=lambda x: x['rsi'], reverse=True)
    
    duration = time.time() - start_time
    logger.info(f"扫描完成: {duration:.2f} 秒")
    logger.info(f"  扫描股票: {len(stock_data)}")
    logger.info(f"  BUY 信号: {len(buy_signals)}")
    logger.info(f"  SELL 信号: {len(sell_signals)}")
    logger.info(f"  HOLD 信号: {len(hold_signals)}")
    
    # 返回前 N 个 BUY 信号
    return buy_signals[:max_signals]


# ============================================================================
# Telegram 通知
# ============================================================================

def format_signal_message(signal: Dict) -> str:
    """格式化信号消息（加入一键看图链接）"""
    ticker = signal['ticker']
    tv_url = f"https://www.tradingview.com/chart/?symbol={ticker}"
    yf_url = f"https://finance.yahoo.com/quote/{ticker}"
    
    return f"""
🔥 <b>BUY 信号触发</b>

📈 <b>代码: {ticker}</b>
💰 现价: ${signal['price']:.2f}
📊 RSI (动能): {signal['rsi']:.1f}
📅 日期: {signal['date'].strftime('%Y-%m-%d')}

🔍 <b>一键看图表:</b>
<a href="{tv_url}">[打开 TradingView]</a>
<a href="{yf_url}">[打开 Yahoo Finance]</a>
"""

def send_signals(signals: List[Dict], telegram: TelegramNotifier):
    """发送信号到 Telegram"""
    if not signals:
        logger.info("没有发现信号")
        return
    
    logger.info(f"发送 {len(signals)} 个信号到 Telegram")
    
    for signal in signals:
        message = format_signal_message(signal)
        telegram.send_message(message)
        time.sleep(0.5)  # 避免被限流


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Swing Trading Assistant - 实时扫描器")
    logger.info("=" * 60)
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化 Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not telegram_chat_id:
        logger.error("未设置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 环境变量")
        logger.info("请在 .env 文件中设置:")
        logger.info("  TELEGRAM_BOT_TOKEN=your_bot_token")
        logger.info("  TELEGRAM_CHAT_ID=your_chat_id")
        return
    
    telegram = TelegramNotifier(telegram_token, telegram_chat_id)
    
    try:
        # 获取股票列表
        tickers = get_russell_1000()
        logger.info(f"扫描 {len(tickers)} 只股票")
        
        # 扫描市场
        signals = scan_market(tickers)
        
        # 发送信号
        send_signals(signals, telegram)
        
        # 发送总结
        summary = f"""
✅ <b>市场扫描完成</b>

📊 扫描结果:
  • 扫描股票: {len(tickers)}
  • 发现信号: {len(signals)}

🕐 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        telegram.send_message(summary)
        
        logger.info("=" * 60)
        logger.info("扫描完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"扫描失败: {e}", exc_info=True)
        telegram.send_message(f"❌ 扫描失败: {str(e)}")


if __name__ == "__main__":
    # 加载 .env 文件
    from dotenv import load_dotenv
    load_dotenv()
    
    main()