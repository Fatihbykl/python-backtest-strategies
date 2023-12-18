import pandas as pd
import numpy as np
import pandas_ta
from backtesting import Backtest
from backtesting.lib import Strategy, TrailingStrategy
from indicators import indicators
from talib import _ta_lib as ta


def calc_vwma(close, volume, length):
    pv = close * volume
    vwma = ta.SMA(pv, 50) / ta.SMA(volume, 50)
    return vwma


class Test(TrailingStrategy):
    trailing_long_sl = 0.95
    trailing_short_sl = 1.05
    trailing_activation_long = 1.01
    trailing_activation_short = 0.99

    def init(self):
        super().init()
        self.coral = self.I(
            indicators.coral_trend,
            self.data,
            plot=True
        )


    def next(self):
        super().next()
        vwma = calc_vwma(self.data.Close, self.data.Volume, 20)
        coral = self.coral[-1]
        price = self.data.Close[-1]
        if vwma is None:
            return

        # for trade in self.trades:
        #     if price / trade.entry_price > self.trailing_activation_long:
        #         if trade.is_long:
        #             trade.sl = max(trade.sl, price * self.trailing_long_sl)
        #     if price / trade.entry_price > self.trailing_activation_short:
        #         if trade.is_short:
        #             trade.sl = min(trade.sl, price * self.trailing_short_sl)

        if len(self.trades) == 0:
            if price > vwma[-1] and coral == 1:
                sl1 = price * self.trailing_long_sl
                self.buy(sl=sl1)
            elif price < vwma[-1] and coral == -1:
                sl1 = price * self.trailing_short_sl
                self.sell(sl=sl1)


df = pd.read_csv('../csv_data/ADAUSDT_1d_(2022-12-18,2023-12-18).csv')
df = df.loc[:, ['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
df.index = pd.to_datetime(df['timestamp'])
bt = Backtest(df, Test, cash=1_000_000)

stats = bt.run()
print(stats)
bt.plot()
