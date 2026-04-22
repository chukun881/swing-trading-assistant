"""
信号生成模块
整合Pullback、Breakout检测和Exit策略
"""
from typing import Dict, List, Optional
from .indicators import get_latest_indicators
from .pullback import detect_pullback, analyze_pullback_potential
from .breakout import detect_breakout, analyze_breakout_potential


def generate_buy_signals(df, config: dict, symbol: str) -> Optional[Dict]:
    """
    生成买入信号
    
    Args:
        df: 包含技术指标的DataFrame
        config: 配置字典
        symbol: 股票代码
        
    Returns:
        dict: 买入信号信息，如果没有信号则返回None
    """
    indicators = get_latest_indicators(df)
    if not indicators:
        return None
    
    # 检测Pullback信号
    pullback_signal = detect_pullback(indicators, config)
    if pullback_signal:
        pullback_signal['symbol'] = symbol
        return pullback_signal
    
    # 检测Breakout信号
    breakout_signal = detect_breakout(indicators, config)
    if breakout_signal:
        breakout_signal['symbol'] = symbol
        return breakout_signal
    
    return None


def generate_exit_signals(df, config: dict, position: Dict, symbol: str) -> Optional[Dict]:
    """
    生成退出信号
    
    条件：
    - price < EMA20 → SELL
    - RSI > 75 → TAKE PROFIT
    - -5% → STOP LOSS
    
    Args:
        df: 包含技术指标的DataFrame
        config: 配置字典
        position: 持仓信息字典（包含entry_price, quantity等）
        symbol: 股票代码
        
    Returns:
        dict: 退出信号信息，如果没有退出信号则返回None
    """
    indicators = get_latest_indicators(df)
    if not indicators:
        return None
    
    close = indicators['close']
    ema20 = indicators.get('ema20')
    rsi = indicators.get('rsi')
    entry_price = position.get('entry_price')
    
    if not entry_price:
        return None
    
    # 获取配置参数
    stop_loss_pct = config['exit']['stop_loss_pct']
    take_profit_rsi = config['exit']['take_profit_rsi']
    
    # 计算盈亏百分比
    pnl_pct = (close - entry_price) / entry_price
    
    # 检查止损条件
    if pnl_pct <= -stop_loss_pct:
        return {
            'signal': 'STOP LOSS',
            'symbol': symbol,
            'price': close,
            'entry_price': entry_price,
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_pct * position.get('quantity', 0) * entry_price,
            'reason': f"Stop Loss triggered at ${close:.2f}\n"
                     f"• Entry: ${entry_price:.2f}\n"
                     f"• PnL: {pnl_pct*100:.2f}% (Limit: -{stop_loss_pct*100:.1f}%)",
            'action': 'SELL'
        }
    
    # 检查止盈条件（RSI过高）
    if rsi and rsi > take_profit_rsi:
        return {
            'signal': 'TAKE PROFIT',
            'symbol': symbol,
            'price': close,
            'entry_price': entry_price,
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_pct * position.get('quantity', 0) * entry_price,
            'reason': f"Take Profit triggered at ${close:.2f}\n"
                     f"• Entry: ${entry_price:.2f}\n"
                     f"• PnL: {pnl_pct*100:.2f}%\n"
                     f"• RSI ({rsi:.1f}) > {take_profit_rsi} (Overbought)",
            'action': 'SELL'
        }
    
    # 检查技术性卖出条件
    if ema20 and close < ema20:
        return {
            'signal': 'SELL',
            'symbol': symbol,
            'price': close,
            'entry_price': entry_price,
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_pct * position.get('quantity', 0) * entry_price,
            'reason': f"Sell signal at ${close:.2f}\n"
                     f"• Entry: ${entry_price:.2f}\n"
                     f"• PnL: {pnl_pct*100:.2f}%\n"
                     f"• Price (${close:.2f}) < EMA20 (${ema20:.2f})",
            'action': 'SELL'
        }
    
    return None


def analyze_stock_potential(df, config: dict, symbol: str) -> Dict:
    """
    分析股票潜力（用于监控和报告）
    
    Args:
        df: 包含技术指标的DataFrame
        config: 配置字典
        symbol: 股票代码
        
    Returns:
        dict: 股票潜力分析结果
    """
    indicators = get_latest_indicators(df)
    if not indicators:
        return {
            'symbol': symbol,
            'pullback_potential': 'LOW',
            'breakout_potential': 'LOW',
            'overall': 'HOLD'
        }
    
    pullback_analysis = analyze_pullback_potential(indicators, config)
    breakout_analysis = analyze_breakout_potential(indicators, config)
    
    # 确定整体建议
    if pullback_analysis['potential'] == 'HIGH' or breakout_analysis['potential'] == 'HIGH':
        overall = 'MONITOR'
    else:
        overall = 'HOLD'
    
    return {
        'symbol': symbol,
        'price': indicators['close'],
        'rsi': indicators.get('rsi'),
        'pullback_potential': pullback_analysis['potential'],
        'pullback_reason': pullback_analysis['reason'],
        'breakout_potential': breakout_analysis['potential'],
        'breakout_reason': breakout_analysis['reason'],
        'overall': overall
    }


def format_signal_message(signal: Dict) -> str:
    """
    格式化信号消息用于Telegram发送
    
    Args:
        signal: 信号字典
        
    Returns:
        str: 格式化的消息
    """
    if signal['signal'] in ['BUY', 'WAIT RETEST']:
        emoji = "📈" if signal['signal'] == 'BUY' else "⏳"
        title = f"{emoji} {signal['strategy']} Signal: {signal['signal']}"
        message = f"{title}\n\n"
        message += f"📌 Symbol: {signal['symbol']}\n"
        message += f"💰 Price: ${signal['price']:.2f}\n"
        message += f"🎯 Confidence: {signal['confidence']}\n\n"
        message += f"📊 Analysis:\n{signal['reason']}"
        
    elif signal['signal'] in ['SELL', 'STOP LOSS', 'TAKE PROFIT']:
        emoji = "🔴" if signal['signal'] in ['STOP LOSS', 'SELL'] else "💰"
        title = f"{emoji} {signal['signal']} Signal"
        message = f"{title}\n\n"
        message += f"📌 Symbol: {signal['symbol']}\n"
        message += f"💰 Current Price: ${signal['price']:.2f}\n"
        message += f"📥 Entry Price: ${signal['entry_price']:.2f}\n"
        message += f"📊 PnL: {signal['pnl_pct']*100:+.2f}% (${signal['pnl_amount']:.2f})\n\n"
        message += f"📊 Analysis:\n{signal['reason']}"
    
    else:
        message = f"Signal: {signal['signal']}\n{signal.get('reason', '')}"
    
    return message