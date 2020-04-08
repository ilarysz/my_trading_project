# Built-in libraries
import json
from datetime import datetime
import pickle
from time import sleep
# Third-party libraries
import pandas as pd
import numpy as np
import requests
from matplotlib import pyplot as plt
from matplotlib import style
# Custom packages
from api_methods import RequestInstrument, MakeOrder, ClosePositions
# Global variables
from shared_variables_secret import QUANDL_API_KEY
from shared_variables import major_pairs, granularity

style.use('fivethirtyeight')


class FundamentalAnalysis:
    def __init__(self, plotting=True):
        self.currency_data = None
        self.interest_rates = None
        self.merged_df = None
        self.corr_df = None
        self.merged_df_resampled = None
        self.hpi_df = None
        self.api_connector = RequestInstrument()
        self.plotting = plotting

    def load_from_api(self):
        # Create class to read from API and send request for <1000 candles
        self.currency_data = self.api_connector.perform_request(candles_count=900, set_granularity='D', pair_choice=0)

    def load_from_quandl(self):
        # Note on 2018-11-10: there are problems with dataset on Quandl (only one existing record)
        # Using quandl API to get interest rates data
        # Prepare request parameters
        params = dict(start_date='2018-01-01', end_date='2018-11-10', api_key=QUANDL_API_KEY)
        url = 'https://www.quandl.com/api/v3/datasets/RBA/F01_FIRMMCTRI'
        # Make a request and read the content (json)
        response = requests.request(method='GET', url=url, params=params)
        response_content = json.loads(response.content)
        # Extract from the dict only relevant part (interest rates)
        self.interest_rates = response_content['dataset']['data']

    def create_df_and_save(self):
        # Takes results from functions "load_from_api" and "load_from_quandl" to create unified dataframe
        # First create df basing on currency and format it's data to match format YYYY-MM-DD
        currency_data_df = pd.DataFrame(data=self.currency_data)
        currency_data_df['time'] = \
            currency_data_df['time'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime('%Y-%m-%d'))
        # Currently column "changed" can be dropped (until results are not written to DB)
        currency_data_df.drop('changed', 1, inplace=True)
        # Create dataframe basing on macro data and merge it the former
        macro_df = pd.DataFrame(data=self.interest_rates)
        macro_df.columns = ['time', 'IR']
        merged = pd.merge(currency_data_df, macro_df, on=["time"])
        # Pickle the resultant DF
        with open('merged_df.pickle', 'wb') as pickle_file:
            pickle.dump(merged, pickle_file)

    def load_merged_from_file(self):
        # Load file crated by the function "create_df"
        pickle_file = open('merged_df.pickle', 'rb')
        self.merged_df = pickle.load(pickle_file)
        pickle_file.close()

        # Convert column values to float
        # Try/except clause to eliminate errors from string conversion attempt
        for column in list(self.merged_df.columns):
            try:
                self.merged_df[column] = self.merged_df[column].astype('float64')
            except ValueError:
                continue
        # Convert time to datetime64
        self.merged_df['time'] = self.merged_df['time'].astype('datetime64')

    def analyse_currency_macro(self):
        # Count percentage change on close price
        self.merged_df['c_pct_change'] = abs(self.merged_df['c'] - self.merged_df['c'][0]) / \
                                         self.merged_df['c'][0] * 100.0

        # Drop unnecessary columns to allow correlation counting between prices and IR
        self.corr_df = self.merged_df.drop(['time', 'c_pct_change'], axis=1)
        self.corr_df = self.corr_df.corr()

        # Plot results and subsequently return create correlation DF
        if self.plotting is True:
            plt.plot(self.merged_df['c_pct_change'])
            plt.legend().remove()
            plt.show()

    def resample(self):
        # Change TF from daily to annual
        # Annual resampling using mean method
        resampled_df = self.merged_df.resample("A", on='time').mean()
        #  Merge annual means with base DF
        self.merged_df_resampled = pd.merge(self.merged_df, resampled_df, on="time", how='outer')
        self.merged_df_resampled.sort_values(by='time', inplace=True, ascending=True)
        # Plot resampled values
        if self.plotting is True:
            ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=6, colspan=1)
            ax1.plot(self.merged_df_resampled.index, self.merged_df_resampled['c_x'])
            plt.show()

    def remove_outlayers(self):
        # Remove outlayers basing formula "current price rolling stdev" > "stdev of stdev for all observations"
        self.merged_df['c_std'] = self.merged_df['c'].rolling(2).std()
        # Remove values where c has std higher than average std for c
        self.merged_df = self.merged_df[(self.merged_df['c_std'] > self.merged_df.describe(include='all').
                                         at['std', 'c_std'])]

    def load_hpi(self):
        url = 'https://www.quandl.com/api/v3/datasets/FMAC/HPI'
        response = requests.request(method='GET', url=url)
        response = json.loads(response.content)
        self.hpi_df = pd.DataFrame(data=response['dataset']['data'])
        self.hpi_df.columns = response['dataset']['column_names']
        self.hpi_df.set_index('Date', inplace=True)

    def complete_data_load(self):
        self.load_from_api()
        self.load_from_quandl()
        self.create_df_and_save()

    def full_loop_with_save_load(self):
        # Load data from the file
        self.load_merged_from_file()
        # Analysis lines, each one can be used separately
        self.analyse_currency_macro()
        # self.load_hpi()
        self.resample()
        self.remove_outlayers()


class IndicatorsCalculator:
    @staticmethod
    def create_bottom_indicator(pricing_data_frame, bottom_indicator):
        # Computation for the indicators
        if bottom_indicator[0] == 'macd':
            # Method of calculating MACD: Subtract slower EMA from faster what created MACD Line. Signal line is EMA
            # from the MACD Line. Histogram is supportive and represents difference between MACD Line and signal line
            # Information about the periods comes from the users who was first shown with the popup window
            # that take inputs and write them to global variables
            # Calculate slow EMA, skip first records (number of record skipped equals to period of EMA)
            pricing_data_frame['macd_ema_slow'] = pricing_data_frame['c'].ewm(span=bottom_indicator[1],
                                                                              adjust=False,
                                                                              min_periods=bottom_indicator[1],
                                                                              ignore_na=True).mean()
            # Calculate fast EMA, also skip first records (number of record skipped equals to period of EMA)
            pricing_data_frame['macd_ema_fast'] = pricing_data_frame['c'].ewm(span=bottom_indicator[2],
                                                                              adjust=False,
                                                                              min_periods=bottom_indicator[2],
                                                                              ignore_na=True).mean()
            # MACD line is difference of slow and fast ema
            pricing_data_frame['macd_line'] = pricing_data_frame['macd_ema_slow'] - pricing_data_frame['macd_ema_fast']
            # Singal line is EMA of MACD Line
            pricing_data_frame['signal_line'] = pricing_data_frame['macd_line'].ewm(span=bottom_indicator[3],
                                                                                    adjust=False,
                                                                                    min_periods=bottom_indicator[3],
                                                                                    ignore_na=True).mean()
            # Histogram is difference of MACD Line and Signal Line
            pricing_data_frame['histogram'] = pricing_data_frame['macd_line'] - pricing_data_frame['signal_line']
            return pricing_data_frame

        elif bottom_indicator[0] == 'rsi':
            # Method of calculating RSI: in n-day window close-open values are calculated,
            # separate n-day moving averages for upsides and downsides are created. Relation of it is called "RS"
            # which is about to be used in 100 - (100/(1 + RS))

            # np.apply_along_axis: 0 - across columns, 1 across rows
            # Function used for comparisons
            def compare(x):
                # By default returns proper results for "up" column
                if x > 0:
                    return x
                else:
                    return np.nan

            # Basing on the close-open comparison create lists that are passed into array
            # "Down" x value is modified to return proper value from function, RSI has no negative value so returned x
            # is converted just after it is returned and passed to the list
            # In averages NaN is returned if there was only one type of candle, it is converted to,
            # proper in that case, 0

            # Convert column values to floats
            pricing_data_frame['c'] = [float(x) for x in pricing_data_frame['c']]
            pricing_data_frame['o'] = [float(x) for x in pricing_data_frame['o']]
            # Subtract close price from open and determine if it increased or decreased, create separate arrays for each
            pricing_data_frame['up'] = [compare(x) for x in pricing_data_frame['c'] - pricing_data_frame['o']]
            pricing_data_frame['down'] = [abs(compare(-x)) for x in pricing_data_frame['c'] - pricing_data_frame['o']]
            # Calculate rolling averages for each of arrays
            pricing_data_frame['up_average'] = pricing_data_frame['up'].rolling(bottom_indicator[1],
                                                                                min_periods=1).mean()
            pricing_data_frame['down_average'] = pricing_data_frame['down'].rolling(bottom_indicator[1],
                                                                                    min_periods=1).mean()
            # Convert nans in arrays to 0, inplace
            np.nan_to_num(pricing_data_frame['up_average'], False)
            np.nan_to_num(pricing_data_frame['down_average'], False)
            # RSI calculation and scaling it to 0-100
            pricing_data_frame['RS'] = pricing_data_frame['up_average'] / pricing_data_frame['down_average']
            pricing_data_frame['RSI'] = 100 - (100 / (1 + pricing_data_frame['RS']))

            return pricing_data_frame

    @staticmethod
    def create_chart_indicator(pricing_data_frame, chart_indicator):
        # Computation for chart indicators. Parameters are set earlier by user which shown a pop-up windows that
        # allows to change periods
        if chart_indicator[0] == 'sma':
            # Rolling simple moving average
            sma = pricing_data_frame['c'].rolling(chart_indicator[1]).mean()
            return sma
        elif chart_indicator[0] == 'ema':
            # Rolling exponential moving average
            # Options allow to show NaN on the head data
            ema = pricing_data_frame['c'].ewm(span=chart_indicator[1], adjust=False, min_periods=chart_indicator[1],
                                              ignore_na=True).mean()
            return ema


class TradingEngine(FundamentalAnalysis, IndicatorsCalculator):
    def __init__(self):
        super().__init__()

    def simple_decision_on_ma(self, pair=2, span=14, calc_method="sma", granularity_choice=0, units=1000):
        # Makes a buy if pair is above the Simple Moving Average and sale in contrary situation
        api_connector = RequestInstrument()
        history_data = api_connector.perform_request(pair_choice=pair,
                                                     candles_count=span,
                                                     set_granularity=granularity[granularity_choice])
        ma = self.create_chart_indicator(history_data, [calc_method, span])
        # The last record is still not closed therefore the -2 is taken
        last_c_price = float(history_data.loc[len(history_data) - 2, "c"])
        last_ma_price = ma[len(ma)-1]
        mo = MakeOrder()
        if last_ma_price > last_c_price:
            print("Selling %s" % major_pairs[pair])
            mo.perform_request(pair, units=(-1)*units)
        elif last_ma_price < last_c_price:
            print("buy %s " % major_pairs[pair])
            mo.perform_request(pair, units=units)
        else:
            print("Prices equal, decision on hold on %s " % major_pairs[pair])

    @staticmethod
    def simple_closing_module(pair):
        cp = ClosePositions()
        print("Closing sell position on %s " % major_pairs[pair])
        cp.perform_request(pair, "close_sell")
        print("Closing buy position on %s " % major_pairs[pair])
        cp.perform_request(pair, "close_buy")

    def run_decision_engine_in_loop(self, sleep_time=15):
        while True:
            for i in range(len(major_pairs)):
                self.simple_decision_on_ma(pair=i)
            sleep(sleep_time)

            for i in range(len(major_pairs)):
                self.simple_closing_module(i)


if __name__ == '__main__':
    # fm = FundamentalAnalysis()
    # fm.complete_data_load()
    # fm.full_loop_with_save_load()
    te = TradingEngine()
    te.run_decision_engine_in_loop()
