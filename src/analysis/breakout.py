"""
Breakout检测模块
检测符合Breakout策略的买入信号
"""
from typing import Dict, Optional


def detect_breakout(indicators: Dict, config: Dict) -> Optional[Dict]:
    """
    检测Breakout买入信号
    
    条件：
    - price > EMA50
    - close > upper band
    - RSI 60–75
    - （可选）band squeeze
    
    Args:
        indicators: 技术指标字典
        config: 配置字典
        
    Returns:
        dict: 如果检测到信号，返回信号信息；否则返回None
    """
    # 检查数据完整性
    if not all([indicators.get('close'), indicators.get('ema50'), 
                indicators.get('rsi'), indicators.get('bb_upper'),
                indicators.get('bb_width')]):
        return None
    
    close = indicators['close']
    ema50 = indicators['ema50']
    rsi = indicators['rsi']
    bb_upper = indicators['bb_upper']
    bb_width = indicators['bb_width']
    
    # 获取配置参数
    rsi_min = config['breakout']['rsi_min']
    rsi_max = config['breakout']['rsi_max']
    check_band_squeeze = config['breakout']['check_band_squeeze']
    band_squeeze_threshold = config['breakout']['band_squeeze_threshold']
    
    # 检查基础条件
    condition1 = close > ema50  # price > EMA50
    condition2 = close > bb_upper  # close > upper band
    condition3 = rsi_min <= rsi <= rsi_max  # RSI 60–75
    
    # 可选：检查band squeeze
    condition4 = True
    if check_band_squeeze:
        condition4 = bb_width < band_squeeze_threshold
    
    # 所有条件满足
    if all([condition1, condition2, condition3, condition4]):
        # 判断是BUY还是WAIT RETEST
        # 如果RSI较高（接近上限），建议等待回测
        signal_type = 'BUY'
        if rsi > (rsi_max - 5):  # RSI > 70
            signal_type = 'WAIT RETEST'
            confidence = 'MEDIUM'
        else:
            confidence = 'HIGH'
        
        reason_lines = [
            f"Breakout detected at ${close:.2f}",
            f"• Price > EMA50: {condition1}",
            f"• Price > BB Upper: {condition2}",
            f"• RSI ({rsi:.1f}) in range [{rsi_min}, {rsi_max}]"
        ]
        
        if check_band_squeeze:
            reason_lines.append(
                f"• BB Width ({bb_width:.3f}) {'<' if condition4 else '>='} {band_squeeze_threshold}"
            )
        
        return {
            'signal': signal_type,
            'strategy': 'BREAKOUT',
            'price': close,
            'reason': '\n'.join(reason_lines),
            'confidence': confidence,
            'indicators': {
                'price': close,
                'ema50': ema50,
                'rsi': rsi,
                'bb_upper': bb_upper,
                'bb_width': bb_width
            }
        }
    
    return None


def analyze_breakout_potential(indicators: Dict, config: Dict) -> Dict:
    """
    分析Breakout潜力（用于监控）
    
    Args:
        indicators: 技术指标字典
        config: 配置字典
        
    Returns:
        dict: Breakout潜力分析结果
    """
    if not all([indicators.get('close'), indicators.get('ema50'), 
                indicators.get('rsi'), indicators.get('bb_upper')]):
        return {'potential': 'LOW', 'reason': 'Insufficient data'}
    
    close = indicators['close']
    ema50 = indicators['ema50']
    rsi = indicators['rsi']
    bb_upper = indicators['bb_upper']
    
    # 计算接近上轨的程度
    distance_to_upper = (bb_upper - close) / bb_upper
    
    # 评估潜力
    if (close > ema50 and 50 < rsi < 70 and 
        distance_to_upper < 0.05):
        return {
            'potential': 'HIGH',
            'reason': f'Near breakout zone (RSI: {rsi:.1f}, distance to BB upper: {distance_to_upper*100:.1f}%)'
        }
    elif (close > ema50 and 50 < rsi < 75 and 
          distance_to_upper < 0.15):
        return {
            'potential': 'MEDIUM',
            'reason': f'Building momentum (RSI: {rsi:.1f}, distance to BB upper: {distance_to_upper*100:.1f}%)'
        }
    else:
        return {
            'potential': 'LOW',
            'reason': f'Not in breakout setup'
        }