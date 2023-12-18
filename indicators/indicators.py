import numpy as np
import pandas as pd
import math
from talib import _ta_lib as ta


def ema_chain(data):
    ema_89 = ta.EMA(data, 89)
    ema_100 = ta.EMA(data, 100)
    ema_120 = ta.EMA(data, 120)
    ema_150 = ta.EMA(data, 150)
    ema_200 = ta.EMA(data, 200)

    return ema_89, ema_100, ema_120, ema_150, ema_200


def uhl_ma_crossover_system(src, length=100, mult=1.0):
    df = pd.DataFrame({'src': src})
    df['sma'] = df['src'].rolling(window=length).mean()
    df['var'] = df['src'].rolling(window=length).var() * mult

    cma = np.zeros(len(src))
    cts = np.zeros(len(src))

    for i in range(100, len(src)):
        sec_ma = (df['sma'].iloc[i] - cma[i - 1]) ** 2
        sects = (df['src'].iloc[i] - cts[i - 1]) ** 2
        ka = 1 - df['var'].iloc[i] / sec_ma if df['var'].iloc[i] < sec_ma else 0
        kb = 1 - df['var'].iloc[i] / sects if df['var'].iloc[i] < sects else 0

        cma[i] = ka * df['sma'].iloc[i] + (1 - ka) * cma[i - 1]
        cts[i] = kb * df['src'].iloc[i] + (1 - kb) * cts[i - 1]

    df['cma'] = cma
    df['cts'] = cts
    return df['cts'], df['cma']


# Range Filter
def range_size(df: pd.DataFrame, range_period: float, range_multiplier: int):
    wper = range_period * 2 - 1
    # last candle is last index, not 0
    average_range = ta.EMA(df.diff().abs(), range_period)
    AC = ta.EMA(average_range, wper) * range_multiplier
    return AC


def range_filter(x: pd.DataFrame, r: pd.DataFrame):
    range_filt = x.copy()
    hi_band = x.copy()
    lo_band = x.copy()
    signals = x.copy()
    trend = x.copy()

    for i in range(x.size):
        if i < 1:
            continue
        if math.isnan(r[i]):
            continue
        if x[i] > nz(range_filt[i - 1]):
            if x[i] - r[i] < nz(range_filt[i - 1]):
                range_filt[i] = nz(range_filt[i - 1])
            else:
                range_filt[i] = x[i] - r[i]
        else:
            if x[i] + r[i] > nz(range_filt[i - 1]):
                range_filt[i] = nz(range_filt[i - 1])
            else:
                range_filt[i] = x[i] + r[i]

        hi_band[i] = range_filt[i] + r[i]
        lo_band[i] = range_filt[i] - r[i]

        fdir = 0.0
        if range_filt.iloc[i] > range_filt.iloc[i - 1]:
            fdir = 1
        elif range_filt.iloc[i] < range_filt.iloc[i - 1]:
            fdir = -1

        upward = 1 if fdir == 1 else 0
        downward = 1 if fdir == -1 else 0

        # Trading Condition
        longCond = (x.iloc[i] > range_filt.iloc[i] and x.iloc[i] > x.iloc[i - 1] and upward > 0) or (
                range_filt.iloc[i] < x.iloc[i] < x.iloc[i - 1] and upward > 0)
        shortCond = (x.iloc[i] < range_filt.iloc[i] and x.iloc[i] < x.iloc[i - 1] and downward > 0) or (
                range_filt.iloc[i] > x.iloc[i] > x.iloc[i - 1] and downward > 0)

        if longCond:
            trend.iloc[i] = 1
        elif shortCond:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i - 1]

        longCondition = longCond and trend.iloc[i - 1] == -1
        shortCondition = shortCond and trend.iloc[i - 1] == 1
        if longCondition:
            signals.iloc[i] = 1.0
        elif shortCondition:
            signals.iloc[i] = -1.0
        else:
            signals.iloc[i] = 0
    return signals


def nz(x) -> float:
    res = x
    if math.isnan(x):
        res = 0.0

    return res


def range_filter_swing(df, swing_period, swing_multiplier):
    smrng = range_size(df, swing_period, swing_multiplier)
    signals = range_filter(df, smrng)
    return signals


########################################################

def produce_signal_st(supertrend, close_array):
    son_kapanis = close_array[-1]
    onceki_kapanis = close_array[-2]

    son_supertrend_deger = supertrend[-1]
    onceki_supertrend_deger = supertrend[-2]

    # renk yeşile dönüyor, trend yükselişe geçti
    if son_kapanis > son_supertrend_deger and onceki_kapanis < onceki_supertrend_deger:
        return 1.0

    # renk kırmızıya dönüyor, trend düşüşe geçti
    elif son_kapanis < son_supertrend_deger and onceki_kapanis > onceki_supertrend_deger:
        return -1.0

    else:
        return 0


def generate_supertrend(close_array, high_array, low_array, atr_period, atr_multiplier):
    atr = ta.atr(high_array, low_array, close_array, atr_period)

    previous_final_upper_band = 0
    previous_final_lower_band = 0
    final_upper_band = 0
    final_lower_band = 0
    previous_close = 0
    previous_supertrend = 0
    supertrend = []
    supertrendc = 0

    for i in range(0, len(close_array)):
        if np.isnan(close_array[i]):
            pass
        else:
            highc = high_array[i]
            lowc = low_array[i]
            atrc = atr[i]
            closec = close_array[i]

            if math.isnan(atrc):
                atrc = 0

            basic_upperband = (highc + lowc) / 2 + atr_multiplier * atrc
            basic_lowerband = (highc + lowc) / 2 - atr_multiplier * atrc

            if basic_upperband < previous_final_upper_band or previous_close > previous_final_upper_band:
                final_upper_band = basic_upperband
            else:
                final_upper_band = previous_final_upper_band

            if basic_lowerband > previous_final_lower_band or previous_close < previous_final_lower_band:
                final_lower_band = basic_lowerband
            else:
                final_lower_band = previous_final_lower_band

            if previous_supertrend == previous_final_upper_band and closec <= final_upper_band:
                supertrendc = final_upper_band
            else:
                if previous_supertrend == previous_final_upper_band and closec >= final_upper_band:
                    supertrendc = final_lower_band
                else:
                    if previous_supertrend == previous_final_lower_band and closec >= final_lower_band:
                        supertrendc = final_lower_band
                    elif previous_supertrend == previous_final_lower_band and closec <= final_lower_band:
                        supertrendc = final_upper_band

            supertrend.append(supertrendc)
            previous_close = closec
            previous_final_upper_band = final_upper_band
            previous_final_lower_band = final_lower_band
            previous_supertrend = supertrendc

    return supertrend


def coral_trend(data):
    # Define your input parameters

    src = pd.Series(data=data['Close'], index=data.index)
    sm = 7  # You can input the value as needed
    cd = 0.4  # You can input the value as needed

    # Create a DataFrame to store intermediate values
    df = pd.DataFrame(index=data.index, columns=['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'bfr', 'signal'])

    # Calculate di, c1, c2, c3, c4, and c5
    di = (sm - 1.0) / 2.0 + 1.0
    c1 = 2 / (di + 1.0)
    c2 = 1 - c1
    c3 = 3.0 * (cd * cd + cd * cd * cd)
    c4 = -3.0 * (2.0 * cd * cd + cd + cd * cd * cd)
    c5 = 3.0 * cd + 1.0 + cd * cd * cd + 3.0 * cd * cd

    for index in range(14, len(df)):
        df['i1'].iloc[index] = c1 * src.iloc[index] + c2 * nz(df['i1'].iloc[index - 1])
        df['i2'].iloc[index] = c1 * df['i1'].iloc[index] + c2 * nz(df['i2'].iloc[index - 1])
        df['i3'].iloc[index] = c1 * df['i2'].iloc[index] + c2 * nz(df['i3'].iloc[index - 1])
        df['i4'].iloc[index] = c1 * df['i3'].iloc[index] + c2 * nz(df['i4'].iloc[index - 1])
        df['i5'].iloc[index] = c1 * df['i4'].iloc[index] + c2 * nz(df['i5'].iloc[index - 1])
        df['i6'].iloc[index] = c1 * df['i5'].iloc[index] + c2 * nz(df['i6'].iloc[index - 1])

        df['bfr'].iloc[index] = -cd * cd * cd * df['i6'].iloc[index] + c3 * df['i5'].iloc[index] + c4 * df['i4'].iloc[
            index] + c5 * \
                                df['i3'].iloc[index]
        df['signal'].iloc[index] = np.where(df['bfr'].iloc[index] > nz(df['bfr'].iloc[index - 1]), 1,
                                            np.where(df['bfr'].iloc[index] < nz(df['bfr'].iloc[index - 1]), -1, 0))
    return df['signal']
