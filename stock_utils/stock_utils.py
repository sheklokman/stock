import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta

"""
author - Rocky Shek
date - 2023-01-27
"""

def timestamp(dt):
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000)

def linear_regession(x, y):
    lr = LinearRegression()
    lr.fit(x,y)
    return lr.coef_[0][0]

def n_day_regression(n, df, idxs):
    _varname_ = f'{n}_reg'
    df[_varname_] = np.nan

    for idx in idxs:
        if idx > n:
            y = df['Close'][idx-n: idx].to_numpy()
            x = np.arange(0, n)
            #reshape
            y = y.reshape(y.shape[0], 1)
            x = x.reshape(x.shape[0], 1)
            # calculate regerssion coefficients
            coef = linear_regession(x, y)
            df.iloc[idx, df.columns.get_loc(_varname_)] = coef

    return df

def normalixed_value(high, low, close):
    epsilon = 10e-10 # to avoide deletion by 0

    # normalixed value = (Close - Low) / (High - Low)
    return (close - low) / (high - low + epsilon)

def get_stock_price(ticker, date):
    start_date = date - timedelta(days = 10)
    end_date = date

    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)

    return hist['Close'].values[-1]

def get_stock_price_history(ticker, start_date = None, end_date = None, n = 10):
    
    stock = yf.Ticker(ticker)
    if start_date:
        hist = stock.history(start = start_date, end = end_date)
    else:
        hist = stock.history(period="max")
    
    hist['normalized_value'] = hist.apply(lambda x: normalixed_value(x['High'], x['Low'], x['Close']), axis = 1)
    hist['loc_min'] = hist.iloc[argrelextrema(hist['Close'].values, np.less_equal, order = n)[0]]['Close']
    hist['loc_max'] = hist.iloc[argrelextrema(hist['Close'].values, np.greater_equal, order =n)[0]]['Close']

    idx_with_mins = np.where(hist['loc_min'] > 0)[0]
    idx_with_maxs = np.where(hist['loc_max'] > 0)[0]

    return hist, idx_with_mins, idx_with_maxs
    
def create_train_data(ticker, start_date = None, end_date = None, n = 10):
    # get stock data
    data, idxs_with_mins, idxs_with_maxs = get_stock_price_history(ticker, start_date, end_date, n)

    #create regressions for 3, 5, 10 and 20 days
    data = n_day_regression(3, data, list(idxs_with_mins) + list(idxs_with_maxs))
    data = n_day_regression(5, data, list(idxs_with_mins) + list(idxs_with_maxs))
    data = n_day_regression(10, data, list(idxs_with_mins) + list(idxs_with_maxs))
    data = n_day_regression(20, data, list(idxs_with_mins) + list(idxs_with_maxs))

    _data_ = data[(data['loc_min'] > 0) | (data['loc_max'] > 0)].reset_index(drop = True)

    # create a dummy variable for local_min (0) and max (1)
    _data_['target'] = [1 if x > 0 else 0 for x in _data_['loc_max']]

    #columns of interest
    cols_of_interest = ['Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg', 'target']
    _data_ = _data_[cols_of_interest]

    return _data_.dropna(axis = 0)

def create_test_data_lr(ticker, start_date = None, end_date = None, n = 10):
    #get data to a dataframe
    data, _, _ = get_stock_price_history(ticker, start_date, end_date, n)
    idxs = np.arange(0, len(data))

    #create regressions for 3, 5, 10 and 20 days
    data = n_day_regression(3, data, idxs)
    data = n_day_regression(5, data, idxs)
    data = n_day_regression(10, data, idxs)
    data = n_day_regression(20, data, idxs)

    cols = ['Close', 'Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg']
    data = data[cols]

    return data.dropna(axis = 0)

def predict_trend(ticker, _model_, start_date = None, end_date = None, n = 10):

    #get data
    data, _, _ = get_stock_price_history(ticker, start_date, end_date, n)
    idxs = np.arange(0, len(data))

    #create regressions for 3, 5, 10, 20 days
    data = n_day_regression(3, data, idxs)
    data = n_day_regression(5, data, idxs)
    data = n_day_regression(10, data, idxs)
    data = n_day_regression(20, data, idxs)

    #create a column for predicted value
    data['pred'] = np.nan

    #get data
    cols = ['Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg']
    x = data[cols]

    #scale the x data
    scaler = MinMaxScaler()
    x = scaler.fit_transform(x)

    for i in range(x.shape[0]):
        try:
            data['pred'][i] = _model_.predict(x[i, :])
        except:
            data['pred'][i] = np.nan
    
    return data


    
