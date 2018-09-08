from functools import wraps
from flask import session, redirect
import threading
from queue import Queue
from Data_Reader import DataHandler
import numpy as np
import pandas as pd
from shared_variables import major_pairs, granularity

q = Queue()
print_lock = threading.Lock()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


class ThreadedMACalculator:

    def __init__(self, ma_type, interval):
        self.ma_type = ma_type
        self.interval = interval

        self.df = pd.DataFrame(np.zeros((len(major_pairs), len(granularity)), dtype=bool),
                               columns=granularity, index=major_pairs)
        # self.df['symbol'] = major_pairs
        # cols = granularity
        # cols.insert(0, 'symbol')
        # self.df = self.df[cols]

    def calculate_single_pair_mas(self, pair):
        data_handler = DataHandler()
        # One thread per pair. Each for iteration downloads data for given granularity, creates MA for it and then
        # compares it to close price. If close price is higher True is written into data frame, else False
        for timeframe in granularity:
            # Candles count takes into account requirement from indicators to have extra data
            # In bottom_indicator the highest number is always stored on [1] position
            history_data = data_handler.read_from_api(request_type='history', pair_choice=pair,
                                                      candles_count=self.interval*2, set_granularity=timeframe,
                                                      streaming_type="pricing")
            if self.ma_type == 'sma':
                sma = history_data['c'].rolling(self.interval).mean()
                comparison_result = float(history_data.at[self.interval * 2 - 1, 'c']) > float(
                    sma.iat[self.interval * 2 - 1])
                self.df.at[major_pairs[pair], timeframe] = comparison_result
                # with print_lock:
                #     print("Calculated sma of period {} for pair {}".format(self.interval, pair))
                #     print("SMA", sma, "SMA last record: ", float(sma.iat[self.interval*2-1]))
                #     print("DF", history_data['c'], "DF last record: ", float(history_data.at[self.interval*2-1,'c']))
                #    comparison_result = float(history_data.at[self.interval*2-1,'c']) > \
                #                        float(sma.iat[self.interval*2-1])
                #     print("Comparison result: ", comparison_result)
            elif self.ma_type == 'ema':
                # Options allow to show NaN on the head data
                ema = history_data['c'].ewm(span=self.interval, adjust=False, min_periods=self.interval,
                                            ignore_na=True).mean()
                comparison_result = float(history_data.at[self.interval * 2 - 1, 'c']) > float(
                    ema.iat[self.interval * 2 - 1])
                self.df.at[major_pairs[pair], timeframe] = comparison_result
            else:
                raise RuntimeError("Wrong moving average type passed to the function!")

    def ma_threader(self):
        while True:
            worker = q.get()
            self.calculate_single_pair_mas(pair=worker)
            q.task_done()

    def calculate_mas(self):
        for i in range(len(major_pairs)):
            t = threading.Thread(target=self.ma_threader)
            t.daemon = True
            t.start()

        for pair in range(len(major_pairs)):
            q.put(pair)

        q.join()
        return self.df


class ThreadedPricingRequest:

    def __init__(self):
        self.pricing_list = []

    def request_pricing(self, pair):
        data_handler = DataHandler()
        self.pricing_list.append(data_handler.read_from_api(request_type='pricing', pair_choice=pair))

    def pricing_threader(self):
        while True:
            worker = q.get()
            self.request_pricing(worker)
            q.task_done()

    def core(self, *args, **kwargs):
        for x in major_pairs:
            t = threading.Thread(target=self.pricing_threader)
            t.daemon = True
            t.start()

        for worker in range(len(major_pairs)):
            q.put(worker)

        q.join()
        self.pricing_list = sorted(self.pricing_list, key=lambda k: k['pair'])
        return self.pricing_list
