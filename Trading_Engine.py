import json
from requests import request
import Utils
import pandas as pd
from datetime import datetime
from shared_variables import major_pairs


class RequestInstrument:
    def __init__(self):
        self.path = None
        self.method = None
        self.header = None
        self.params = None  # Query
        self.data = None
        self.df_candles = None
        self.major_pairs = major_pairs

    def __repr__(self):
        """Prints carried data frame, checking purposes"""
        print(self.df_candles)

    def set_path(self, pair_choice):
        """Sets the path for the request, only the pair is string is required to be modified. Pair name to be
        received from the interface. No account number need or query string. Other tools are Order and Position
        Book but they only represent Oanda client positions and therefore are useless."""
        self.path = ("https://api-fxpractice.oanda.com/v3/instruments/%s/candles" % self.major_pairs[pair_choice])
        return self.path

    # Rest of the path strings that can be used:
    # def set_path_account(self, choice):
    #     self.path = "https://api-fxpractice.oanda.com/v3/accounts/{}/".format(Utils.account_id)
    #     return self.path
    #
    # def set_path_default(self, choice):
    #     self.path = "https://api-fxpractice.oanda.com/v3/"
    #     return self.path

    def set_method(self):
        """For instrument request there is only method 'GET' available"""
        self.method = 'GET'
        return self.method

    def set_header(self):
        """Method that not requires any changes across all request types. Token and account number is set in another
        file that is not uploaded"""
        self.header = {'Authorization': Utils.token, "Accept-Datetime-Format": "RFC3339"}
        return self.header

    def set_params(self, candles_count=150, set_granularity='H1'):
        """All param types are included here http://developer.oanda.com/rest-live-v20/instrument-ep/. Number
        of candles shall fit the quarter of the screen."""
        # Params can be extended with 'includeFirst': True
        # A flag that controls whether the candlestick that is covered by the from time should be included in the
        # results. This flag enables clients to use the timestamp of the last completed candlestick received to poll
        # for future candlesticks but avoid receiving the previous candlestick repeatedly. [default=True]
        self.params = {'price': 'B', 'granularity': set_granularity, 'count': candles_count, 'smooth': 'False',
                       'dailyAlignment': 17, 'alignmentTimezone': 'America/New_York', 'weeklyAlignment': 'Friday'}
        return self.params

    def perform_request(self, candles_count, set_granularity, pair_choice):
        """Launches all functions that prepare HTTP request to be performed and the make the request. Received data
        are converted to data frame with another method and then shall be taken by interface"""
        self.set_path(pair_choice)
        self.set_method()
        self.set_header()
        self.set_params(candles_count, set_granularity)
        self.convert_to_data_frame(json.loads(
            request(self.method, self.path, headers=self.header, params=self.params).content))
        return self.df_candles

    def convert_to_data_frame(self, r_json):
        """Converts data from the requests do data frame"""
        # Create empty data frame with the following columns and set the index
        self.df_candles = pd.DataFrame(columns=['id', 'time', 'volume', 'o', 'h', 'l', 'c'])
        self.df_candles = self.df_candles.set_index('id')
        # The structure of received data is following: dictionary of 'candles' and in each of it: 'time', 'volume'
        # and at another dictionary 'ask'/'bid'/'mid' (according to given argument) that contains OHLC
        # enumerate allows to choose the index, temp stores the values for every columns that written at once
        for pos, candle in enumerate(r_json['candles']):
            temp = [candle['time'], candle['volume']]
            for price in candle['bid'].values():
                temp.append(price)
            self.df_candles.loc[pos] = temp
        # Only converting to datetime object without formatting:
        # self.df_candles['time'] = self.df_candles['time'].apply(
        # (lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f000Z')))
        # At the end date and time column is converted to more convenient format
        self.df_candles['time'] = self.df_candles['time'].apply(
            (lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f000Z').strftime('%Y-%m-%d %H:%M')))
        self.df_candles['changed'] = 1


class RequestPricing:
    def __init__(self):
        self.path = None
        self.method = None
        self.header = None
        self.params = None  # Query
        self.data = None
        self.df_candles = None
        self.major_pairs = major_pairs
        self.pricing = None

    def __repr__(self):
        """Prints carried data frame, checking purposes"""
        print(self.df_candles)

    def set_path(self, type_choice):
        """Sets the path basing on the choice send from the interface, pairs are sent in query string"""
        if type_choice == 'pricing':
            self.path = "https://api-fxpractice.oanda.com/v3/accounts/{}/pricing".format(Utils.account_id)
        elif type_choice == 'streaming':
            # The sites suggest address containing "fxtrade", to check (!)
            self.path = "https://stream-fxpractice.oanda.com/v3/accounts/{}/pricing/stream".format(Utils.account_id)
        return self.path

    def set_method(self):
        """For pricing request there is only method 'GET' available"""
        self.method = 'GET'
        return self.method

    def set_header(self):
        """Method that not requires any changes across all request types. Token and account number is set in another
        file that is not uploaded"""
        self.header = {'Authorization': Utils.token, "Accept-Datetime-Format": "RFC3339"}
        return self.header

    def set_params(self, type_choice, pair_choice):
        """All param types are included here http://developer.oanda.com/rest-live-v20/pricing-ep/. Number
        of candles shall fit the quarter of the screen. Bases on the same choice as set_path method"""
        # Flag that enables the inclusion of the unitsAvailable field in the returned Price objects. [default=True]
        # Deprecated: Will be removed in a future API update.
        date = datetime.now().date()
        # The date for regular weekdays are set with now function, for weekends is one day backward
        if date.weekday() == 5:
            date = date.replace(day=date.day-1)
        elif date.weekday() == 6:
            date = date.replace(day=date.day-2)
        # The tuple contains sorted currency pairs, they can only be accessed one at the time as requests library
        # sends the query in wrong format (repeats keyword "instrument") and the only last pair is recognized by API
        if type_choice == 'pricing':
            self.params = {'instruments': self.major_pairs[pair_choice], 'since': str(date),
                           'includeUnitsAvailable': True, 'includeHomeConversions': 'False'}
        elif type_choice == 'streaming':
            self.params = {'instruments': self.major_pairs[pair_choice], 'snapshot': True}
        return self.params

    def perform_request(self, type_choice='pricing', pair_choice=0):
        """Launches all functions that prepare HTTP request to be performed and the make the request. Received data
        are converted to /dictionary/ with another method and then shall be taken by interface"""
        self.set_path(type_choice)
        self.set_method()
        self.set_header()
        self.set_params(type_choice, pair_choice)
        r = request(self.method, self.path, headers=self.header, params=self.params)
        # print(r)
        # print(r.url)
        r_loaded = json.loads(r.content)
        self.pricing = {'pair': r_loaded['prices'][0]['instrument'], 'bid': r_loaded['prices'][0]['bids'][0]['price'],
                        'asks': r_loaded['prices'][0]['asks'][0]['price']}
        return self.pricing


# r = RequestInstrument()
# r.perform_request(pair_choice=1, candles_count=150, set_granularity='H1')
# print(r)

#
# s = RequestPricing()
# pricing = s.perform_request()
# print(pricing)
