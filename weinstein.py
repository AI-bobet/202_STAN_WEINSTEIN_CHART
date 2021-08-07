# %%
import os
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import sqlalchemy
# %%
engine = sqlalchemy.create_engine('postgresql://{0}:{1}@{2}:{3}/trading'.format(os.environ.get('db_user'), os.environ.get('db_password'),
                                                                                os.environ.get('db_host'), os.environ.get('db_port')))
# %%
time_frame = 'D'  # D-Daily, #W-Weekly #Monthly,
timespan = 'TTM'  # TTM - Trailing 12 months, #YTD - YearToDate, #5Y, Max
# %% Show valid inputs to the user:


def display_valid_sectors(valid_PSE_sectors):

    print('Here are the valid indexes for Philipine Stock Exhange:')
    print(' ')
    print(valid_PSE_sectors)
    print(' ')
    print('Choose and Press ENTER')
# %% Ask user what indexes they want to analyze:


def user_input_index():

    valid_PSE_sectors = ['[0] PSEi', '[1] ALL SHARES', '[2] FINANCIALS', '[3] INDUSTRIAL',
                         '[4] HOLDING FIRMS', '[5] SERVICES', '[6] MINING AND OIL', '[7] PROPERTY']

    indexes = ['PSE.PSEi', 'PSE.ALL', 'PSE.FIN', 'PSE.IND',
               'PSE.HDG', 'PSE.SVC', 'PSE.M-O', 'PSE.PRO']

    display_valid_sectors(valid_PSE_sectors)

    user = 'wrong'

    while user not in ['0', '1', '2', '3', '4', '5', '6', '7']:

        user = input('Please Enter Valid PSE Sector: ')

        if user not in ['0', '1', '2', '3', '4', '5', '6', '7']:
            clear_output()
            print('')
            print('Enter Valid PSE Sector:')
            print('')
            print(valid_PSE_sectors)

    return indexes[int(user)]

# %% Show Available time frame


def display_available_time_frame(available_time_frame):

    print('What is your preferred timeframe?')
    print(' ')
    print(available_time_frame)
    print(' ')
    print('Choose One and Press ENTER')
# %% Ask user there's preferred timeframe


def user_time_frame():

    available_time_frame = ['[D] DAILY', '[W] WEEKLY', '[M] MONTHLY']

    display_available_time_frame(available_time_frame)

    user = 'wrong'

    while user not in ['D', 'W', 'M']:

        user = input('Please Enter Your Preferred Timeframe:')

        if user not in ['D', 'W', 'M']:
            clear_output()
            print('')
            print('Enter Valid Timeframe:')
            print('')
            print(available_time_frame)

    return user
# %%


def sector_data(sector_user_input):

    # load data
    q_data = '''SELECT * FROM pse_index_data
                WHERE ticker = {0}{1}{2}
                ORDER BY date'''.format("'", sector_user_input, "'")

    data = pd.read_sql_query(q_data, engine, index_col='date', dtype={
                             'date': np.datetime64})
    data = data.drop(['ticker'], axis=1)

    # Filter data based from user's prefer timeframe using panda's df.resample method
    # Dictionary
    aggregation = {'open': 'first',
                   'high': 'max',
                   'low': 'min',
                   'close': 'last'}
    # 'Volume':'sum'}
    data = data.resample(time_frame).agg(aggregation)
    data = data.dropna()

    return data

# %% Market Average Could be PSEi or PSE All Shares


def Market_Average(average="PSE.PSEi"):

    # load data
    q_data = '''SELECT * FROM pse_index_data
                WHERE ticker = {0}{1}{2}
                ORDER BY date'''.format("'", average, "'")

    data = pd.read_sql_query(q_data, engine, index_col='date', dtype={
                             'date': np.datetime64})
    data = data.drop(['ticker'], axis=1)

    # Filter data based from user's prefer timeframe using panda's df.resample method
    # Dictionary
    aggregation = {'open': 'first',
                   'high': 'max',
                   'low': 'min',
                   'close': 'last'}
    # 'Volume':'sum'}
    data = data.resample(time_frame).agg(aggregation)
    data = data.dropna()
    return data
# %%This function returns the trading days of the derivatives in list


def list_trading_days(data):

    # Get the all the value of Sector's index column
    Available_Data = data.index

    # Convert Datetime index into string with date format YYYY-MM-DD
    Available_Data = Available_Data.strftime('%Y-%m-%d')

    # Covert the sets of data into List
    Available_Data = Available_Data.tolist()

    return Available_Data
# %%This function returns the preferred number of datapoints (timeperiod) by the user


def time_period(timespan, sector_data):

    rows = len(sector_data)

    if rows <= 244 or timespan == 'Max':
        data_points = -(rows)
    elif rows >= 244 and timespan == 'TTM':
        data_points = -244
    elif rows > 244 and rows < 1220 and timespan == '5Y':
        data_points = -(rows)
    elif rows >= 1220 and timespan == '5Y':
        data_points = -1220

    return data_points

# %%This function compares trading days of two dataframes and return their similar values in a list


def date_values(data):

    Stock_index = list_trading_days(data)
    PSE_Average = list_trading_days(Market_Average())

    Similar_Trading_Dates = set(Stock_index) & set(PSE_Average)

    # Convert set into List
    Similar_Trading_Dates = list(Similar_Trading_Dates)

    # Sort List in ascending order
    Similar_Trading_Dates.sort()

    # return Similar_Trading_Dates[time_period('5Y', Similar_Trading_Dates):]

    return Similar_Trading_Dates

# %%This function return the value of dataframe based from user's preferred datapoints (timeperiod)


def PSE_sector(data):

    sector_df = data.loc[date_values(data), :]

    return sector_df
# %%This function compute the Mansfield Relative Strenth


def Mansfield_RS(sector_data):

    # This Functions match the number of available data in Index to Market Average
    PSE_Average = Market_Average().loc[date_values(sector_data), :]

    # Relative Performance
    Dorsey_RS = sector_data[['close']].div(PSE_Average['close'].values, axis=0)

    # Dorsey 200 day Simple Moving Average
    Dorsey_SMA = Dorsey_RS.rolling(window=200).mean()

    # Compute for Mansfield Relative Strenth
    # Mansfield Relative Performance = (( Today's Standard Relative Performance divided by Today's Standard Relative Performance 52 Week Moving Average )) - 1) * 100
    Mansfield_RS = ((Dorsey_RS.div(Dorsey_SMA.values, axis=0))-1)*100

    # Drop NaN
    Mansfield_RS = Mansfield_RS.dropna()

    return Mansfield_RS

# %%Create Charts


def graph_Data():

    sector_user_input = user_input_index()
    data = sector_data(sector_user_input)
    index_data = PSE_sector(data)
    RS = Mansfield_RS(index_data)

    max_date = RS.index.max()
    min_date = RS.index.min()

    # Convert Timestamp/Datetime to String
    max_date = pd.to_datetime(max_date).strftime('%Y-%m-%d')
    min_date = pd.to_datetime(min_date).strftime('%Y-%m-%d')

    # Filter sector data in parallel with the number of data in RS
    index_data = index_data.loc[min_date:max_date]

    ap = mpf.make_addplot(RS, panel=1, type='line')

    # Create my own `marketcolors` to use with the `nightclouds` style:
    mc = mpf.make_marketcolors(up='#00ff00', down='#ff2e2e', inherit=True)

    # Create a new style based on `nightclouds` but with my own `marketcolors`:
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

    fig, axes = mpf.plot(index_data,
                         mav=(30),
                         type='candle',
                         ylabel='Price',
                         panel_ratios=(5, 2),
                         figratio=(2, 1),
                         figscale=1.5,
                         style=s,
                         addplot=ap,
                         tight_layout=True,
                         xrotation=60,
                         returnfig=True)

    labels = ["SMA 30"]

    axes[0].legend(labels, loc='upper left')
    axes[2].legend(["Mansfield's Relative Strength [vs PSEi]"],
                   fontsize=9, loc='upper left')
    #axes[3].legend(['MACD', 'Signal Line'], fontsize=6, loc='lower right')

    axes[0].set_title(f"\nPSE {sector_user_input} INDEX")
    #axes[2].set_title(" Mansfield's Relative Strength [vs PSEi]")
    plt.show()


# %%
if __name__ == '__main__':
    graph_Data()

# %%
