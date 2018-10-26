import pandas as pd
import requests
import json
from datetime import datetime
import pickle
from matplotlib import pyplot as plt
from matplotlib import style
style.use('fivethirtyeight')
# Module currently is stand-alone, in future it will be run server.py with data from there
from Data_Reader import DataHandler


def load_from_api():
    data_handler = DataHandler()
    currency_data = data_handler.read_from_api(candles_count=900, set_granularity='D')
    return currency_data


def load_from_quandl():
    # url = 'https://www.quandl.com/api/v3/datatables/AUSBS/D'
    # params = dict(date='1994-11-15', series_id='A85002072C', api_key='GysehMr_Z5bQybBkbUqk')
    # params_encoded = urllib.parse.urlencode(params).encode("UTF-8")
    # r = urllib.request.Request(url, data=params_encoded)
    # print(r.get_full_url())
    # response = urllib.request.urlopen(r)
    # print(response.read())

    # params = dict(date='1994-11-15', series_id=','.join(['A85002072C', 'A84999997V']), api_key='GysehMr_Z5bQybBkbUqk')
    # response = requests.request(method='GET', url='https://www.quandl.com/api/v3/datatables/AUSBS/D',
    #                             params=params, headers=headers)
    # Interest Rates And Yields – Money Market - Daily - Total Return Index. Units: Index 04-Jan-2011=100
    headers = {'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) "
                             "Chrome/24.0.1312.27 Safari/537.17"}
    params = dict(start_date='2011-01-01', end_date='2018-10-03', api_key='GysehMr_Z5bQybBkbUqk')
    url = 'https://www.quandl.com/api/v3/datasets/RBA/F01_FIRMMCTRI'

    response = requests.request(method='GET', url=url, params=params, headers=headers)

    # print(response.url)
    response_content = json.loads(response.content)
    interest_rates = response_content['dataset']['data']
    return interest_rates


def create_df(currency_data, macro):
    currency_data_df = pd.DataFrame(data=currency_data)
    currency_data_df['time'] = \
        currency_data_df['time'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime('%Y-%m-%d'))
    currency_data_df.drop('changed', 1, inplace=True)
    macro_df = pd.DataFrame(data=macro)
    macro_df.columns = ['time', 'IR']
    # print(currency_data_df.head(5), '\n', macro_df.head(5))
    merged = pd.merge(currency_data_df, macro_df, on=["time"])
    with open('merged_df.pickle', 'wb') as pickle_file:
        pickle.dump(merged, pickle_file)

    return 0


def load_merged_from_file():
    pickle_file = open('merged_df.pickle', 'rb')
    merged_df = pickle.load(pickle_file)
    pickle_file.close()

    return merged_df


def analyse_currency_macro(merged_df):
    for column in list(merged_df.columns):
        try:
            merged_df[column] = merged_df[column].astype('float64')
        except ValueError:
            continue
    merged_df['c_pct_change'] = abs(merged_df['c'] - merged_df['c'][0]) / merged_df['c'][0] * 100.0

    corr_df = merged_df.drop(['time', 'c_pct_change'], axis=1)
    corr_df = corr_df.corr()

    plt.plot(merged_df['c_pct_change'])
    plt.legend().remove()
    plt.show()

    return corr_df


def resample(merged_df):
    merged_df['c'] = merged_df['c'].astype('float64')
    merged_df['time'] = merged_df['time'].astype('datetime64')
    resampled_df = merged_df.resample("A", on='time').mean()
    merged_df_resampled = pd.merge(merged_df, resampled_df, on="time", how='outer')
    merged_df_resampled.sort_values(by='time', inplace=True, ascending=True)
    ax1 = plt.subplot2grid((6,1), (0,0), rowspan=6, colspan=1)
    ax1.plot(merged_df_resampled.index, merged_df_resampled['c_x'])
    plt.show()

    return merged_df_resampled


def rolling_stats(merged_df):
    merged_df['SMA_12'] = merged_df['c'].rolling(7).mean()

    return merged_df


def remove_outlayers(merged_df):
    merged_df['c'] = merged_df['c'].astype('float64')
    merged_df['c_std'] = merged_df['c'].rolling(2).std()
    # Remove values where c has std higher than average std for c
    merged_df = merged_df[(merged_df['c_std'] > merged_df.describe(include='all').at['std', 'c_std'])]

    return merged_df


def analyse_macro(macro):
    macro_df = pd.DataFrame(data=macro)
    macro_df.columns = ['Date', 'IR']
    macro_df.set_index('Date', inplace=True)

    return macro_df


def load_hpi():
    # Create list of US states for request
    # scrapped = pd.read_html("https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States")
    # states = scrapped[0][1].iloc[2:]
    # # for index_value in states.index.values:
    # #     print(states.iloc[index_value])
    # for index in range(len(states)):
    #     ''.join(['FMAC/',states.iloc[index]])
    # url = 'https://www.quandl.com/api/v3/datasets/FMAC/HPI'
    # request = urllib.request.Request(url)
    # response = urllib.request.urlopen(request)
    # print(json.loads(response.read()))
    url = 'https://www.quandl.com/api/v3/datasets/FMAC/HPI'
    response = requests.request(method='GET', url=url)
    response = json.loads(response.content)
    hpi_df = pd.DataFrame(data=response['dataset']['data'])
    hpi_df.columns = response['dataset']['column_names']
    hpi_df.set_index('Date', inplace=True)
    return hpi_df

# Uncomment next 3 lines to retrieve API data and write it into file
# currency_data = load_from_api()
# interest_rates = load_from_quandl()
# create_df(currency_data=currency_data, macro=interest_rates)


# Load data from the file
merged_df = load_merged_from_file()


# Analysis lines, each one can be used separately
# analyse_currency_macro(merged_df=merged_df)
# analyse_macro(macro=interest_rates)
# load_hpi()
# resample(merged_df=merged_df)
# rolling_stats(merged_df)
merged_df_removed_outlayers = remove_outlayers(merged_df=merged_df)
print(merged_df_removed_outlayers.head(5))
print(merged_df_removed_outlayers.describe())
