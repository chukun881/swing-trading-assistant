"""
技术指标计算模块
计算EMA、RSI、Bollinger Bands等技术指标
"""
import pandas as pd
import numpy as np
import talib


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """计算指数移动平均线 (EMA)"""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """计算相对强弱指数 (RSI)"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> dict:
    """
    计算布林带 (Bollinger Bands)
    
    Returns:
        dict: 包含 upper, middle, lower 三个序列
    """
    middle = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def calculate_all_indicators(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    计算所有技术指标
    
    Args:
        df: 包含OHLCV数据的DataFrame
        config: 配置字典
        
    Returns:
        添加了技术指标的DataFrame
    """
    df = df.copy()
    
    # 获取配置参数
    ema_short = config['indicators']['ema_short']
    ema_long = config['indicators']['ema_long']
    rsi_period = config['indicators']['rsi_period']
    bb_period = config['indicators']['bollinger_period']
    bb_std = config['indicators']['bollinger_std']
    
    # 计算EMA
    df[f'EMA{ema_short}'] = calculate_ema(df['close'], ema_short)
    df[f'EMA{ema_long}'] = calculate_ema(df['close'], ema_long)
    
    # 计算RSI
    df['RSI'] = calculate_rsi(df['close'], rsi_period)
    
    # 计算Bollinger Bands
    bb = calculate_bollinger_bands(df['close'], bb_period, bb_std)
    df['BB_Upper'] = bb['upper']
    df['BB_Middle'] = bb['middle']
    df['BB_Lower'] = bb['lower']
    
    # 计算Band Width (用于检测band squeeze)
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
    
    return df


def get_latest_indicators(df: pd.DataFrame) -> dict:
    """
    获取最新的技术指标值
    
    Args:
        df: 包含技术指标的DataFrame
        
    Returns:
        dict: 最新指标值
    """
    if len(df) < 2:
        return None
    
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    
    return {
        'close': latest['close'],
        'ema20': latest.get('EMA20', None),
        'ema50': latest.get('EMA50', None),
        'rsi': latest.get('RSI', None),
        'rsi_previous': previous.get('RSI', None),
        'bb_upper': latest.get('BB_Upper', None),
        'bb_lower': latest.get('BB_Lower', None),
        'bb_middle': latest.get('BB_Middle', None),
        'bb_width': latest.get('BB_Width', None),
        'volume': latest.get('volume', None)
    }