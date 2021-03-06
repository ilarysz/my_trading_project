# Built-in libraries
from functools import wraps
import threading
from queue import Queue
# Third-party libraries
from flask import session, redirect
import oauth2
from urllib import parse
import numpy as np
import pandas as pd
# Custom packages
from api_methods import RequestInstrument, RequestPricing
import shared_variables_secret
# Global variables
from shared_variables import major_pairs, granularity

print_lock = threading.Lock()


def login_required(f):
    # Decorator, check if users is logged in
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
        self.q = Queue()
        self.df = pd.DataFrame(np.zeros((len(major_pairs), len(granularity)), dtype=bool),
                               columns=granularity, index=major_pairs)

    def calculate_single_pair_mas(self, pair):
        api_connector = RequestInstrument()
        # One thread per pair. Each for iteration downloads data for given granularity, creates MA for it and then
        # compares it to close price. If close price is higher True is written into data frame, else False
        for timeframe in granularity:
            # Candles count takes into account requirement from indicators to have extra data
            # In bottom_indicator the highest number is always stored on [1] position
            history_data = api_connector.perform_request(pair_choice=pair, candles_count=self.interval*2,
                                                         set_granularity=timeframe)
            if self.ma_type == 'sma':
                sma = history_data['c'].rolling(self.interval).mean()
                comparison_result = float(history_data.at[self.interval * 2 - 1, 'c']) > float(
                    sma.iat[self.interval * 2 - 1])
                self.df.at[major_pairs[pair], timeframe] = comparison_result

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
            # Take one pair number from the queue
            worker = self.q.get()
            # Calculate MAs within that function and write them
            self.calculate_single_pair_mas(pair=worker)
            self.q.task_done()

    def calculate_mas(self):
        # Launch separate thread for each pair
        for i in range(len(major_pairs)):
            t = threading.Thread(target=self.ma_threader)
            t.daemon = True
            t.start()

        # Add pairs to the queue
        for pair in range(len(major_pairs)):
            self.q.put(pair)

        self.q.join()
        return self.df


class ThreadedPricingRequest:

    def __init__(self):
        self.pricing_list = []
        self.api_connector = RequestPricing()
        self.q = Queue()

    def request_pricing(self, pair):
        self.pricing_list.append(self.api_connector.perform_request(pair_choice=pair))

    def pricing_threader(self):
        while True:
            # Take pair number from the queue
            worker = self.q.get()
            # Process within the given Thread pricing request for that pair and write it down to list
            self.request_pricing(worker)
            # Task for that pair is done
            self.q.task_done()

    def core(self):
        # Launch thread for each pair
        for x in range(4):
            t = threading.Thread(target=self.pricing_threader)
            t.daemon = True
            t.start()

        # Add pair numbers to the queue
        for worker in range(len(major_pairs)):
            self.q.put(worker)

        self.q.join()
        # Sort list before returning it
        self.pricing_list = sorted(self.pricing_list, key=lambda k: k['pair'])
        return self.pricing_list


class TwitterLogin:

    # Class handles process of twitter authorization
    consumer = None
    client = None
    request_token = None
    oauth_verifier = None
    token = None

    @classmethod
    def get_request_token(cls):
        # Create Consumer and Client classes using consumer key and consumer secret key
        cls.consumer = oauth2.Consumer(shared_variables_secret.CONSUMER_KEY, shared_variables_secret.CONSUMER_SECRET)
        cls.client = oauth2.Client(cls.consumer)

        # With Client object acquire request token and request token secret
        response, content = cls.client.request(uri=shared_variables_secret.REQUEST_TOKEN_URL)

        # # Break if server did not respond correctly
        # if response != 200:
        #     return print("Error during obtaining request token.")

        # Using parse_qsl parse request token and request token secret and save it as dictionary
        cls.request_token = dict(parse.parse_qsl(content.decode("UTF-8")))

        # Take authorization address and acquired request token to create ready to use url
        return '{}?oauth_token={}'.format(shared_variables_secret.AUTHORIZATION_URL, cls.request_token["oauth_token"])

    @classmethod
    def get_access_token(cls, oauth_verifier):
        # Create token object using request token and request token secret, then set verifier
        cls.token = oauth2.Token(cls.request_token['oauth_token'], cls.request_token['oauth_token_secret'])
        cls.token.set_verifier(oauth_verifier)
        cls.client = oauth2.Client(cls.consumer, cls.token)

        # Using complete Client object make a request for authorization token
        response, content = cls.client.request(shared_variables_secret.ACCESS_TOKEN_URL, 'POST')

        # Parse received result
        return dict(parse.parse_qsl(content.decode("UTF-8")))
