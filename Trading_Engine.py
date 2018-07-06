import json
import requests
import Utils

url_path = "https://stream-practice.oanda.com/v3/accounts/{}/pricing/stream".format(Utils.account_id)


class Request:
    def __init__(self):
        self.path = None
        self.method = None
        self.header = None
        self.params = None #Query

    def set_path(self):
        url_path = "https://api-fxpractice.oanda.com/v3/"
        url_account_path = "https://api-fxpractice.oanda.com/v3/accounts/{}/".format(Utils.account_id)
        url_instrument_path = "https://api-fxpractice.oanda.com/v3/instruments/"
        url_streaming_path = "https://stream-fxpractice.oanda.com/v3/accounts/{}/pricing/stream".format(Utils.account_id)
        additional_elements = "EUR_USD/candles"
        self.path = url_instrument_path + additional_elements
        return self.path

    def set_method(self):
        self.method = 'GET'
        return self.method

    def set_header(self):
        self.header = {'Authorization': Utils.token}
        return self.header

    def set_params(self):
        self.params = {'granularity': 'D', 'from': '2018-07-02', 'to': '2018-07-06'}
        return self.params

    def perform_request(self):
        self.set_path()
        self.set_method()
        self.set_header()
        self.set_params()
        r = requests.request(self.method, self.path, headers=self.header, params=self.params)
        r_json = json.loads(r.content)
        return r_json['candles'][4]['mid']['c']
