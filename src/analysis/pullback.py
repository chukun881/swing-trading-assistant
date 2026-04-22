"""
Pullback检测模块
检测符合Pullback策略的买入信号
"""
from typing import Dict, Optional


def detect_pullback(indicators: Dict, config: Dict) -> Optional[Dict]:
    """
    检测Pullback买入信号
    
    条件：
    - price > EMA50
    - EMA20 > EMA50
    - price touches lower band (price <= lower_band)
    - RSI < 30 并且回升
    
    Args:
        indicators: 技术指标字典
        config: 配置字典
        
    Returns:
        dict: 如果检测到信号，返回信号信息；否则返回None
    """
    # 检查数据完整性
    if not all([indicators.get('close'), indicators.get('ema20'), 
                indicators.get('ema50'), indicators.get('rsi'),
                indicators.get('rsi_previous'), indicators.get('bb_lower')]):
        return None
    
    close = indicators['close']
    ema20 = indicators['ema20']
    ema50 = indicators['ema50']
    rsi = indicators['rsi']
    rsi_previous = indicators['rsi_previous']
    bb_lower = indicators['bb_lower']
    
    # 获取配置参数
    rsi_oversold = config['pullback']['rsi_oversold']
    rsi_recovery_threshold = config['pullback']['rsi_recovery_threshold']
    
    # 检查条件
    condition1 = close > ema50  # price > EMA50
    condition2 = ema20 > ema50  # EMA20 > EMA50
    condition3 = close <= bb_lower  # price touches lower band
    condition4 = rsi < rsi_oversold  # RSI < 30
    condition5 = (rsi - rsi_previous) >= rsi_recovery_threshold  # RSI回升
    
    # 所有条件满足
    if all([condition1, condition2, condition3, condition4, condition5]):
        return {
            'signal': 'BUY',
            'strategy': 'PULLBACK',
            'price': close,
            'reason': f"Pullback detected at ${close:.2f}\n"
                     f"• Price > EMA50: {condition1}\n"
                     f"• EMA20 > EMA50: {condition2}\n"
                     f"• Price touches BB Lower: {condition3}\n"
                     f"• RSI ({rsi:.1f}) < {rsi_oversold} and recovering\n"
                     f"• RSI change: {rsi - rsi_previous:+.1f}",
            'confidence': 'HIGH',
            'indicators': {
                'price': close,
                'ema20': ema20,
                'ema50': ema50,
                'rsi': rsi,
                'bb_lower': bb_lower
            }
        }
    
    return None


def analyze_pullback_potential(indicators: Dict, config: Dict) -> Dict:
    """
    分析Pullback潜力（用于监控）
    
    Args:
        indicators: 技术指标字典
        config: 配置字典
        
    Returns:
        dict: Pullback潜力分析结果
    """
    if not all([indicators.get('close'), indicators.get('ema20'), 
                indicators.get('ema50'), indicators.get('rsi'),
                indicators.get('bb_lower')]):
        return {'potential': 'LOW', 'reason': 'Insufficient data'}
    
    close = indicators['close']
    ema20 = indicators['ema20']
    ema50 = indicators['ema50']
    rsi = indicators['rsi']
    bb_lower = indicators['bb_lower']
    
    # 计算接近下轨的程度
    distance_to_lower = (close - bb_lower) / bb_lower
    
    # 评估潜力
    if (close > ema50 and ema20 > ema50 and 
        distance_to_lower < 0.05 and rsi < 40):
        return {
            'potential': 'HIGH',
            'reason': f'Near pullback zone (RSI: {rsi:.1f}, BB distance: {distance_to_lower*100:.1f}%)'
        }
    elif (close > ema50 and ema20 > ema50 and 
          distance_to_lower < 0.10 and rsi < 50):
        return {
            'potential': 'MEDIUM',
            'reason': f'Approaching pullback zone (RSI: {rsi:.1f}, BB distance: {distance_to_lower*100:.1f}%)'
        }
    else:
        return {
            'potential': 'LOW',
            'reason': f'Not in pullback setup'
        }