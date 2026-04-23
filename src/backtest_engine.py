"""
Swing Trading Assistant - 回测引擎（愚蠢引擎）

职责：
- 执行交易（买入/卖出）
- 动态计算硬止损（-5%）
- 管理仓位和资金
- 记录交易历史

注意：所有策略逻辑（指标计算、信号生成）都在 src/analysis/breakout.py
"""
import backtrader as bt
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 自定义 PandasData 类（包含信号列）
# ============================================================================

class SignalPandasData(bt.feeds.PandasData):
    """
    扩展的 PandasData，包含 Buy_Signal 和 Sell_Signal 列
    """
    # 定义额外的 lines
    lines = ('Buy_Signal', 'Sell_Signal')
    
    # 定义列名映射
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
        ('Buy_Signal', -1),
        ('Sell_Signal', -1),
    )


# ============================================================================
# IBKR 佣金计算类
# ============================================================================

class IBKRCommission(bt.CommissionInfo):
    """
    IBKR Tiered Pricing 佣金计算
    
    规则：
    - $0.0035 per share
    - Minimum $0.35 per trade
    - Maximum 1% of total trade value
    """
    params = (
        ('per_share', 0.0035),
        ('minimum', 0.35),
        ('max_pct', 0.01),
    )
    
    def _getcommission(self, size, price, pseudoexec):
        """计算佣金"""
        trade_value = abs(size) * price
        commission_by_share = abs(size) * self.p.per_share
        commission_by_pct = trade_value * self.p.max_pct
        commission = min(commission_by_share, commission_by_pct)
        commission = max(commission, self.p.minimum)
        return commission


# ============================================================================
# 回测策略类（愚蠢引擎 - 只执行交易）
# ============================================================================

class SwingTradingStrategy(bt.Strategy):
    """
    简化的回测策略
    
    职责：
    - 读取预计算的 Buy_Signal 和 Sell_Signal
    - 执行买入/卖出
    - 动态计算硬止损（-5%）
    - 管理仓位
    """
    params = (
        ('position_size', 0.10),  # 每次交易使用 10% 资金
    )
    
    def __init__(self):
        # 交易记录
        self.trades = []
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # 记录最大回撤
        self.max_equity = self.broker.getvalue()
        self.max_drawdown = 0.0
        
        # 跟踪当前持仓的入场价格
        self.entry_prices = {}
        self.entry_dates = {}
        
        # 存储所有信号用于排序
        self.buy_signals = []
    
    def next(self):
        """每个 bar 调用"""
        # 更新最大回撤
        current_equity = self.broker.getvalue()
        if current_equity > self.max_equity:
            self.max_equity = current_equity
        drawdown = (self.max_equity - current_equity) / self.max_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # 收集所有信号
        self.buy_signals = []
        
        for data in self.datas:
            # 跳过 VIX 和 SPY（不是股票）
            if data._name in ['VIX', 'SPY']:
                continue
            
            # 检查卖出信号（如果已持有）
            pos = self.getposition(data)
            if pos.size > 0:
                self.check_exit_signals(data, pos)
                continue
            
            # 检查买入信号 - Buy_Signal 可能是 True/False 或 0/1
            buy_signal = False
            if hasattr(data, 'Buy_Signal'):
                try:
                    buy_signal = bool(data.Buy_Signal[0])
                except:
                    pass
            
            if buy_signal:
                self.buy_signals.append({
                    'data': data,
                    'rsi': getattr(data, 'rsi', [50])[0],
                    'price': data.close[0],
                })
        
        # 如果有多个买入信号，按 RSI 排序（最高优先）
        if self.buy_signals:
            self.buy_signals.sort(key=lambda x: x['rsi'], reverse=True)
            
            # 按顺序执行买入
            for signal in self.buy_signals:
                data = signal['data']
                
                # 检查是否有足够现金
                required_cash = self.broker.getvalue() * self.p.position_size
                if self.broker.getcash() < required_cash:
                    continue
                
                # 执行买入
                self.enter_position(data, signal['price'], signal['rsi'])
    
    def enter_position(self, data, price, rsi):
        """入场"""
        # 使用 PercentSizer 自动计算仓位大小
        self.buy(data=data)
        
        # 记录入场信息
        symbol = data._name
        self.entry_prices[symbol] = price
        self.entry_dates[symbol] = data.datetime.date(0)
        
        logger.info(f"ENTER {symbol} at ${price:.2f}, RSI={rsi:.1f}")
    
    def check_exit_signals(self, data, pos):
        """
        检查退出信号
        
        组合：
        1. 预计算的 Sell_Signal (移动止损 EMA20)
        2. 动态硬止损（-5%）
        """
        symbol = data._name
        current_price = data.close[0]
        entry_price = self.entry_prices.get(symbol, pos.price)
        
        exit_reason = None
        
        # 条件1：预计算的移动止损（EMA20）
        if hasattr(data, 'Sell_Signal') and data.Sell_Signal[0] == 1:
            exit_reason = "Trailing Stop (EMA20)"
        
        # 条件2：动态硬止损（-5%）
        elif current_price < (entry_price * 0.95):
            exit_reason = "Stop Loss (-5%)"
        
        if exit_reason:
            self.close_position(data, exit_reason, entry_price)
    
    def close_position(self, data, reason, entry_price):
        """平仓"""
        symbol = data._name
        current_price = data.close[0]
        entry_date = self.entry_dates.get(symbol, data.datetime.date(0))
        
        # 记录交易
        pnl = (current_price - entry_price) / entry_price
        
        trade_info = {
            'symbol': symbol,
            'entry_date': entry_date,
            'exit_date': data.datetime.date(0),
            'entry_price': entry_price,
            'exit_price': current_price,
            'pnl_pct': pnl,
            'reason': reason,
        }
        self.trades.append(trade_info)
        
        # 统计
        self.trade_count += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        logger.info(f"EXIT {symbol} at ${current_price:.2f}, PnL={pnl*100:+.2f}%, Reason={reason}")
        
        # 平仓
        self.close(data=data)
        
        # 清除记录
        if symbol in self.entry_prices:
            del self.entry_prices[symbol]
        if symbol in self.entry_dates:
            del self.entry_dates[symbol]
    
    def stop(self):
        """回测结束时调用"""
        final_value = self.broker.getvalue()
        initial_value = 10000.0
        total_return = (final_value - initial_value) / initial_value * 100
        
        win_rate = 0
        if self.trade_count > 0:
            win_rate = self.winning_trades / self.trade_count * 100
        
        max_dd = self.max_drawdown * 100
        
        # 打印结果
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:+.2f}%")
        print(f"Total Trades: {self.trade_count}")
        print(f"Winning Trades: {self.winning_trades}")
        print(f"Losing Trades: {self.losing_trades}")
        if self.trade_count > 0:
            print(f"Win Rate: {win_rate:.2f}%")
        print(f"Maximum Drawdown: {max_dd:.2f}%")
        print("=" * 60)
        
        # 保存交易记录
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv('backtest_trades.csv', index=False)
            logger.info(f"Trade history saved to backtest_trades.csv")
            
            # 打印最后5笔交易
            print("\nLast 5 Trades:")
            print(trades_df.tail().to_string(index=False))