import pandas as pd
import requests
import json
from datetime import datetime
import pickle
from utils import QUANDL_API_KEY
# Module currently is stand-lone, in future it will be run with server.py with data from there
from data_reader import DataHandler
from matplotlib import pyplot as plt
from matplotlib import style

style.use('fivethirtyeight')


def load_from_api():
    # Create class to read from API and send request for <1000 candles
    data_handler = DataHandler()
    currency_data = data_handler.read_from_api(candles_count=900, set_granularity='D')
    return currency_data


def load_from_quandl():
    # Note on 2018-11-10: there are problems with dataset on Quandl (only one existing record)
    # Using quandl API to get interest rates data
    # Prepare request parameters
    params = dict(start_date='2018-01-01', end_date='2018-11-10', api_key=QUANDL_API_KEY)
    url = 'https://www.quandl.com/api/v3/datasets/RBA/F01_FIRMMCTRI'
    # Make a request and read the content (json)
    response = requests.request(method='GET', url=url, params=params)
    response_content = json.loads(response.content)
    # Extract from the dict only relevant part (interest rates)
    interest_rates = response_content['dataset']['data']
    return interest_rates


def create_df(currency_data, macro):
    # Takes results from functions "load_from_api" and "load_from_quandl" to create unified dataframe
    # First create df basing on currency and format it's data to match format YYYY-MM-DD
    currency_data_df = pd.DataFrame(data=currency_data)
    currency_data_df['time'] = \
        currency_data_df['time'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime('%Y-%m-%d'))
    # Currently column "changed" can be dropped (until results are not written to DB)
    currency_data_df.drop('changed', 1, inplace=True)
    # Create dataframe basing on macro data and merge it the former
    macro_df = pd.DataFrame(data=macro)
    macro_df.columns = ['time', 'IR']
    merged = pd.merge(currency_data_df, macro_df, on=["time"])
    # Pickle the resultant DF
    with open('merged_df.pickle', 'wb') as pickle_file:
        pickle.dump(merged, pickle_file)

    return 0


def load_merged_from_file():
    # Load file crated by the function "create_df"
    pickle_file = open('merged_df.pickle', 'rb')
    merged_df = pickle.load(pickle_file)
    pickle_file.close()

    # Convert column values to float
    # Try/except clause to eliminate errors from string conversion attempt
    for column in list(merged_df.columns):
        try:
            merged_df[column] = merged_df[column].astype('float64')
        except ValueError:
            continue
    # Convert time to datetime64
    merged_df['time'] = merged_df['time'].astype('datetime64')

    return merged_df


def analyse_currency_macro(merged_df):
    # Count percentage change on close price
    merged_df['c_pct_change'] = abs(merged_df['c'] - merged_df['c'][0]) / merged_df['c'][0] * 100.0

    # Drop unnecessary columns to allow correlation counting between prices and IR
    corr_df = merged_df.drop(['time', 'c_pct_change'], axis=1)
    corr_df = corr_df.corr()

    # Plot results and subsequently return create correlation DF
    plt.plot(merged_df['c_pct_change'])
    plt.legend().remove()
    plt.show()

    return corr_df


def resample(merged_df):
    # Change TF from daily to annual
    # Annual resampling using mean method
    resampled_df = merged_df.resample("A", on='time').mean()
    #  Merge annual means with base DF
    merged_df_resampled = pd.merge(merged_df, resampled_df, on="time", how='outer')
    merged_df_resampled.sort_values(by='time', inplace=True, ascending=True)
    # Plot resampled values
    ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=6, colspan=1)
    ax1.plot(merged_df_resampled.index, merged_df_resampled['c_x'])
    plt.show()

    return merged_df_resampled


def remove_outlayers(merged_df):
    # Remove outlayers basing formula "current price rolling stdev" > "stdev of stdev for all observations"
    merged_df['c_std'] = merged_df['c'].rolling(2).std()
    # Remove values where c has std higher than average std for c
    merged_df = merged_df[(merged_df['c_std'] > merged_df.describe(include='all').at['std', 'c_std'])]

    return merged_df


def load_hpi():
    url = 'https://www.quandl.com/api/v3/datasets/FMAC/HPI'
    response = requests.request(method='GET', url=url)
    response = json.loads(response.content)
    hpi_df = pd.DataFrame(data=response['dataset']['data'])
    hpi_df.columns = response['dataset']['column_names']
    hpi_df.set_index('Date', inplace=True)
    return hpi_df


# Uncomment next 3 lines to retrieve API data and write it into file
# 2018-11-10 - experiencing problems with RBA dataset on Quandl - do not run
# currency_data = load_from_api()
# interest_rates = load_from_quandl()
# create_df(currency_data=currency_data, macro=interest_rates)


# Load data from the file
merged_df = load_merged_from_file()

# Analysis lines, each one can be used separately
analyse_currency_macro(merged_df=merged_df)
load_hpi()
resample(merged_df=merged_df)
merged_df_removed_outlayers = remove_outlayers(merged_df=merged_df)
