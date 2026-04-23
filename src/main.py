"""
Swing Trading Assistant - 主程序
整合所有模块，执行市场扫描和信号检测
"""
import os
import sys
import logging
import time
import yaml
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.tradingview import get_stock_list_with_data
from src.data.ibkr import create_ibkr_connection
from src.analysis.indicators import calculate_all_indicators
from src.analysis.signals import generate_buy_signals, generate_exit_signals, analyze_stock_potential
from src.notifications.telegram import create_telegram_notifier


def setup_logging(log_level: str = 'INFO'):
    """配置日志系统"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志文件名（带日期）
    log_filename = os.path.join(log_dir, f'trading_assistant_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置日志格式
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def load_config() -> Dict:
    """加载配置文件"""
    logger = logging.getLogger(__name__)
    
    # 加载YAML配置
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded from config.yaml")
    except Exception as e:
        logger.error(f"Error loading config.yaml: {e}")
        config = {}
    
    # 加载环境变量
    load_dotenv('config/.env')
    
    # 添加环境变量到配置
    env_vars = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
        'IB_HOST': os.getenv('IB_HOST'),
        'IB_PORT': os.getenv('IB_PORT'),
        'IB_CLIENT_ID': os.getenv('IB_CLIENT_ID')
    }
    
    config.update(env_vars)
    logger.info("Environment variables loaded from .env")
    
    return config


def scan_for_signals(config: Dict, telegram_notifier) -> List[Dict]:
    """
    扫描市场寻找交易信号
    
    Args:
        config: 配置字典
        telegram_notifier: Telegram通知器
        
    Returns:
        list: 发现的信号列表
    """
    logger = logging.getLogger(__name__)
    signals = []
    potential_stocks = []
    
    logger.info("Starting market scan...")
    start_time = time.time()
    
    # 获取股票数据
    max_stocks = config.get('max_stocks_per_market', 300)
    stocks = get_stock_list_with_data(config, max_stocks_per_market=max_stocks)
    logger.info(f"Retrieved data for {len(stocks)} stocks")
    
    # 分析每只股票
    for stock in stocks:
        symbol = stock['symbol']
        df = stock['data']
        
        try:
            # 计算技术指标
            df_with_indicators = calculate_all_indicators(df, config)
            
            # 检测买入信号
            buy_signal = generate_buy_signals(df_with_indicators, config, symbol)
            if buy_signal:
                signals.append(buy_signal)
                logger.info(f"BUY signal detected for {symbol}")
                
                # 立即发送信号
                telegram_notifier.send_signal(buy_signal)
            
            # 分析股票潜力
            potential = analyze_stock_potential(df_with_indicators, config, symbol)
            if potential['overall'] == 'MONITOR':
                potential_stocks.append(potential)
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            continue
    
    duration = time.time() - start_time
    logger.info(f"Market scan completed in {duration:.2f} seconds")
    
    # 发送市场扫描报告
    scan_report = telegram_notifier.format_market_scan_report(
        stocks_scanned=len(stocks),
        signals_found=len(signals),
        duration=duration
    )
    telegram_notifier.send_daily_report(scan_report)
    
    # 如果有潜力股票，发送报告
    if potential_stocks:
        potential_report = telegram_notifier.format_potential_stocks_report(potential_stocks)
        telegram_notifier.send_daily_report(potential_report)
    
    return signals


def check_exit_signals(config: Dict, ibkr_connection, telegram_notifier) -> List[Dict]:
    """
    检查持仓的退出信号
    
    Args:
        config: 配置字典
        ibkr_connection: IBKR连接对象
        telegram_notifier: Telegram通知器
        
    Returns:
        list: 退出信号列表
    """
    logger = logging.getLogger(__name__)
    exit_signals = []
    
    if not ibkr_connection:
        logger.warning("IBKR connection not available, skipping exit signal check")
        return exit_signals
    
    try:
        # 获取持仓
        positions = ibkr_connection.get_positions()
        logger.info(f"Checking {len(positions)} positions for exit signals")
        
        for position in positions:
            symbol = position['symbol']
            quantity = position['quantity']
            avg_cost = position['avg_cost']
            
            # 只检查多头持仓
            if quantity <= 0:
                continue
            
            try:
                # 获取股票数据
                from src.data.tradingview import get_stock_historical_data
                df = get_stock_historical_data(symbol)
                
                if df is None:
                    logger.warning(f"Could not get data for position {symbol}")
                    continue
                
                # 计算技术指标
                df_with_indicators = calculate_all_indicators(df, config)
                
                # 准备持仓信息
                position_info = {
                    'entry_price': avg_cost,
                    'quantity': quantity
                }
                
                # 检测退出信号
                exit_signal = generate_exit_signals(df_with_indicators, config, position_info, symbol)
                if exit_signal:
                    exit_signals.append(exit_signal)
                    logger.info(f"Exit signal detected for {symbol}: {exit_signal['signal']}")
                    
                    # 立即发送退出信号
                    telegram_notifier.send_signal(exit_signal)
                
            except Exception as e:
                logger.error(f"Error checking exit signals for {symbol}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in exit signal check: {e}")
    
    return exit_signals


def send_account_report(ibkr_connection, telegram_notifier):
    """
    发送账户报告
    
    Args:
        ibkr_connection: IBKR连接对象
        telegram_notifier: Telegram通知器
    """
    logger = logging.getLogger(__name__)
    
    if not ibkr_connection:
        logger.warning("IBKR connection not available, skipping account report")
        return
    
    try:
        # 获取账户摘要
        summary = ibkr_connection.get_account_summary()
        if summary:
            summary_text = ibkr_connection.format_account_summary(summary)
            telegram_notifier.send_account_summary(summary_text)
        
        # 获取持仓
        positions = ibkr_connection.get_positions()
        if positions:
            positions_text = ibkr_connection.format_positions(positions)
            telegram_notifier.send_positions(positions_text)
        
    except Exception as e:
        logger.error(f"Error sending account report: {e}")


def main():
    """主函数"""
    # 设置日志
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Swing Trading Assistant Started")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 初始化Telegram通知器
    telegram_notifier = create_telegram_notifier(config)
    if not telegram_notifier:
        logger.error("Failed to initialize Telegram notifier")
        return
    
    telegram_notifier.send_success("Swing Trading Assistant started successfully!")
    
    # 连接IBKR（可选）
    ibkr_connection = None
    try:
        ibkr_connection = create_ibkr_connection(config)
        if ibkr_connection:
            logger.info("IBKR connection established")
            # 发送账户报告
            send_account_report(ibkr_connection, telegram_notifier)
        else:
            logger.warning("Could not connect to IBKR, continuing without portfolio tracking")
            telegram_notifier.send_warning("Could not connect to IBKR. Portfolio tracking disabled.")
    except Exception as e:
        logger.error(f"Error connecting to IBKR: {e}")
        telegram_notifier.send_warning(f"IBKR connection error: {e}")
    
    try:
        # 扫描市场寻找买入信号
        buy_signals = scan_for_signals(config, telegram_notifier)
        logger.info(f"Found {len(buy_signals)} buy signals")
        
        # 如果有IBKR连接，检查退出信号
        if ibkr_connection:
            exit_signals = check_exit_signals(config, ibkr_connection, telegram_notifier)
            logger.info(f"Found {len(exit_signals)} exit signals")
        
        logger.info("Swing Trading Assistant completed successfully")
        telegram_notifier.send_success("Market scan completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        telegram_notifier.send_error(f"Execution error: {str(e)}")
    
    finally:
        # 断开IBKR连接
        if ibkr_connection:
            ibkr_connection.disconnect()
            logger.info("IBKR connection closed")
        
        logger.info("=" * 60)
        logger.info("Swing Trading Assistant Finished")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()