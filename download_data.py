import pandas as pd
from binance.client import Client
import datetime
import config


def binance_bar_extractor(symbol):
    b_client = Client(api_key=config.API_KEY, api_secret=config.API_SECRET)

    start_date = datetime.datetime.strptime('18 Dec 2022', '%d %b %Y')
    end_date = datetime.datetime.today()

    interval = Client.KLINE_INTERVAL_1DAY
    filename = 'csv_data/{}_{}_({},{}).csv'.format(symbol, interval, start_date.date(), end_date.date())

    k_lines = b_client.get_historical_klines(symbol, interval,
                                           start_date.strftime("%d %b %Y %H:%M:%S"),
                                           end_date.strftime("%d %b %Y %H:%M:%S"), 1000)
    data = pd.DataFrame(k_lines,
                        columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'quote_av',
                                 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

    data.set_index('timestamp', inplace=True)
    data.to_csv(filename)

    print('finished!')


if __name__ == '__main__':
    binance_bar_extractor('ADAUSDT')
