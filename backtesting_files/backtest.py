import pandas as pd
import numpy as np
from backtesting import Backtest
from backtesting.lib import Strategy, TrailingStrategy
from indicators import indicators
from talib import _ta_lib as ta
from pandas_ta import vwma


class Test(TrailingStrategy):
    atr_f = 0.2

    uhl_ma_length = 100
    uhl_ma_multiplier = 1.0
    swing_period = 50
    swing_multiplier = 3.5

    trailing_long_sl = 0.995
    trailing_short_sl = 1.005
    trailing_activation_long = 1.01
    trailing_activation_short = 0.99

    def init(self):
        super().init()
        self.cts, self.cma = self.I(
            indicators.uhl_ma_crossover_system,
            pd.Series(self.data.Close),
            self.uhl_ma_length,
            self.uhl_ma_multiplier,
            plot=False
        )

        self.range_filter = self.I(
            indicators.range_filter_swing,
            pd.Series(self.data.Close),
            self.swing_period,
            self.swing_multiplier,
            plot=False
        )

    def next(self):
        super().next()
        signal = self.range_filter[-1]
        trend = 'Bull' if self.cts[-1] > self.cma[-1] else 'Bear'
        price = self.data.Close[-1]
        adx = ta.ADX(self.data.High, self.data.Low, self.data.Close, 14)[-1]
        atr = ta.ATR(self.data.High, self.data.Low, self.data.Close, 14)

        for trade in self.trades:
            if price / trade.entry_price > self.trailing_activation_long:
                if trade.is_long:
                    trade.sl = max(trade.sl, price * self.trailing_long_sl)
            if price / trade.entry_price > self.trailing_activation_short:
                if trade.is_short:
                    trade.sl = min(trade.sl, price * self.trailing_short_sl)

        if trend == 'Bull' and signal == 1.0 and len(self.trades) == 0:  # trades number change!
            sl1 = price - atr[-1] / self.atr_f
            sl1 = price * self.trailing_long_sl
            self.buy(sl=sl1)
        elif trend == 'Bear' and signal == -1.0 and len(self.trades) == 0:  # trades number change!
            # sl1 = price + atr[-1] / self.atr_f
            sl1 = price * self.trailing_short_sl
            self.sell(sl=sl1)


df = pd.read_csv('../csv_data/LINKUSDT_15m_(2023-10-05,2023-12-15).csv')
df = df.loc[:, ['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
df.index = pd.to_datetime(df['timestamp'])
bt = Backtest(df, Test, cash=1_000_000)

stats = bt.run()
print(stats)
bt.plot()
