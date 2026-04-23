"""
Telegram通知模块
发送交易信号和状态更新到Telegram
"""
import logging
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional
import asyncio
import sys


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram通知管理类"""
    
    def __init__(self, token: str, chat_id: str):
        """
        初始化Telegram通知器
        
        Args:
            token: Telegram Bot Token
            chat_id: Telegram Chat ID
        """
        self.token = token
        self.chat_id = chat_id
        self.bot = None
        self._initialized = False
        self._loop = None
    
    def _get_or_create_loop(self):
        """获取或创建事件循环"""
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
            return loop
        except RuntimeError:
            # 没有运行中的循环，创建一个新的
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
    
    def initialize(self) -> bool:
        """
        初始化Telegram Bot
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.bot = Bot(token=self.token)
            
            # 使用同步方式测试连接
            loop = self._get_or_create_loop()
            
            async def _get_me():
                return await self.bot.get_me()
            
            result = loop.run_until_complete(_get_me())
            
            self._initialized = True
            logger.info(f"Telegram Bot initialized successfully: {result.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram Bot: {e}")
            return False
    
    async def send_message_async(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        异步发送消息
        
        Args:
            message: 要发送的消息
            parse_mode: 解析模式（Markdown, HTML, 或None）
            
        Returns:
            bool: 发送是否成功
        """
        if not self._initialized:
            logger.error("Telegram Bot not initialized")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info("Message sent to Telegram successfully")
            return True
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        发送消息（同步包装）
        
        Args:
            message: 要发送的消息
            parse_mode: 解析模式
            
        Returns:
            bool: 发送是否成功
        """
        if not self._initialized:
            logger.warning("Telegram Bot not initialized, attempting to initialize...")
            if not self.initialize():
                return False
        
        # 使用现有或创建新的事件循环
        loop = self._get_or_create_loop()
        
        try:
            result = loop.run_until_complete(self.send_message_async(message, parse_mode))
            return result
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return False
        finally:
            # 不关闭循环，让它可以被重用
            # 只清理已完成的任务
            try:
                pending = asyncio.all_tasks(loop)
                # 只取消已经完成的任务
                for task in pending:
                    if task.done():
                        task.cancel()
            except Exception as e:
                logger.debug(f"Error cleaning up tasks: {e}")
    
    def send_signal(self, signal: dict) -> bool:
        """
        发送交易信号
        
        Args:
            signal: 信号字典
            
        Returns:
            bool: 发送是否成功
        """
        from ..analysis.signals import format_signal_message
        
        message = format_signal_message(signal)
        return self.send_message(message)
    
    def send_account_summary(self, summary: str) -> bool:
        """
        发送账户摘要
        
        Args:
            summary: 账户摘要字符串
            
        Returns:
            bool: 发送是否成功
        """
        return self.send_message(summary)
    
    def send_positions(self, positions: str) -> bool:
        """
        发送持仓信息
        
        Args:
            positions: 持仓信息字符串
            
        Returns:
            bool: 发送是否成功
        """
        return self.send_message(positions)
    
    def send_daily_report(self, report: str) -> bool:
        """
        发送每日报告
        
        Args:
            report: 报告字符串
            
        Returns:
            bool: 发送是否成功
        """
        return self.send_message(report)
    
    def send_error(self, error_message: str) -> bool:
        """
        发送错误消息
        
        Args:
            error_message: 错误信息
            
        Returns:
            bool: 发送是否成功
        """
        message = f"🚨 *Error Alert*\n\n{error_message}"
        return self.send_message(message)
    
    def send_success(self, success_message: str) -> bool:
        """
        发送成功消息
        
        Args:
            success_message: 成功信息
            
        Returns:
            bool: 发送是否成功
        """
        message = f"✅ {success_message}"
        return self.send_message(message)
    
    def send_warning(self, warning_message: str) -> bool:
        """
        发送警告消息
        
        Args:
            warning_message: 警告信息
            
        Returns:
            bool: 发送是否成功
        """
        message = f"⚠️ *Warning*\n\n{warning_message}"
        return self.send_message(message)
    
    def format_market_scan_report(self, stocks_scanned: int, signals_found: int, 
                                   duration: float) -> str:
        """
        格式化市场扫描报告
        
        Args:
            stocks_scanned: 扫描的股票数量
            signals_found: 发现的信号数量
            duration: 扫描耗时（秒）
            
        Returns:
            str: 格式化的报告
        """
        lines = [
            "📊 Market Scan Report",
            "",
            f"📈 Stocks Scanned: {stocks_scanned}",
            f"🎯 Signals Found: {signals_found}",
            f"⏱️ Duration: {duration:.2f} seconds",
            ""
        ]
        
        if signals_found > 0:
            lines.append("✨ Trading signals detected!")
        else:
            lines.append("📋 No trading signals at this time.")
        
        return '\n'.join(lines)
    
    def format_potential_stocks_report(self, potential_stocks: list) -> str:
        """
        格式化潜力股票报告
        
        Args:
            potential_stocks: 潜力股票列表
            
        Returns:
            str: 格式化的报告
        """
        if not potential_stocks:
            return "📋 No stocks with high potential detected."
        
        lines = [
            "🎯 High Potential Stocks",
            "",
            f"Found {len(potential_stocks)} stocks worth monitoring:",
            ""
        ]
        
        for stock in potential_stocks[:10]:  # 限制显示前10个
            symbol = stock['symbol']
            price = stock.get('price', 'N/A')
            rsi = stock.get('rsi', 'N/A')
            overall = stock['overall']
            
            emoji = "🔥" if overall == 'MONITOR' else "📋"
            lines.append(f"{emoji} *{symbol}* - ${price} (RSI: {rsi})")
            lines.append(f"   {overall}")
            lines.append("")
        
        return '\n'.join(lines)


def create_telegram_notifier(config: dict) -> Optional[TelegramNotifier]:
    """
    创建Telegram通知器
    
    Args:
        config: 配置字典
        
    Returns:
        TelegramNotifier: 通知器对象，失败返回None
    """
    try:
        token = config.get('TELEGRAM_BOT_TOKEN')
        chat_id = config.get('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in config")
            return None
        
        notifier = TelegramNotifier(token=token, chat_id=chat_id)
        
        if notifier.initialize():
            return notifier
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error creating Telegram notifier: {e}")
        return None