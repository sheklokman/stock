import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from stock_utils.stock_utils import timestamp, create_train_data, get_stock_price_history, create_test_data_lr, create_realtime_data_lr, get_stock_price
from datetime import timedelta, datetime
import time
import os

def load_LR(model_version):

    saved_models_dir = os.path.join(os.getcwd(), 'saved_models')
    model_file = f'lr_{model_version}.sav'
    file = os.path.join(saved_models_dir, model_file)
        
    loaded_model = pickle.load(open(file, 'rb'))

    return loaded_model

def load_scaler(model_version):
    
    saved_scalar_dir = os.path.join(os.getcwd(), 'saved_models')
    scalar_file = f'scaler_{model_version}.sav'
    file = os.path.join(saved_scalar_dir, scalar_file)

    loaded_model = pickle.load(open(file, 'rb'))

    return loaded_model

def _threshold(probs, threshold):
    prob_thresholded = [0 if x > threshold else 1 for x in probs[:, 0]]

    return np.array(prob_thresholded)

def LR_predict(model_version, stock, start_date, end_date, threshold = 0.98, data_type='realtime', hold_till = 10):
    #create model and scaler instances
    scaler = load_scaler(model_version) 
    lr = load_LR(model_version)

    #Interested cols
    if model_version == 'v1':
        interested_cols = ['Close', 'Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg', '50_reg', '100_reg']
    elif model_version == 'v2':
        interested_cols = ['Close', 'Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg']
    else: 
        interested_cols = ['Close', 'Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg', '50_reg', '100_reg']

    #create input
    if(data_type == 'realtime'):
        today = datetime.today().date()
        if model_version == "v1":
            end = today - timedelta(days = 1)
            start = today - timedelta(days = 200)
        elif model_version == "v2":
            end = today - timedelta(days = 1)
            start = today - timedelta(days = 100)
        data = create_realtime_data_lr(stock, start, end, n = hold_till, cols = interested_cols)
    else:
        data = create_test_data_lr(stock, start_date, end_date, n = hold_till, cols = interested_cols )

    #get close price of final date
    close_price = data['Close'].values[-1]

    #get input data to model
    interested_cols.remove('Close')
    input_data = data[interested_cols]
    input_data = input_data.to_numpy()[-1].reshape(1, -1)

    #scale input data
    input_data_scaled = scaler.transform(input_data)
    prediction = lr._predict_proba_lr(input_data_scaled)
    prediction_thresholded = _threshold(prediction, threshold)

    return prediction[:, 0], prediction_thresholded[0], close_price

def LR_sell(stock, buy_date, buy_price, todays_date, sell_perc = 0.1, hold_till = 3, stop_perc = 0.05):
    current_price = get_stock_price(stock, todays_date)
    sell_price = buy_price + buy_price * sell_perc
    stop_price = buy_price - buy_price * stop_perc
    sell_date = buy_date + timedelta(days = hold_till) # selling date
    time.sleep(1) #to make sure the requested transactions per seconds is not exceeded

    if (current_price is not None) and ((current_price < stop_price) or (current_price >= sell_price) or (todays_date >= sell_date)):
        return "SELL", current_price #if criteria is met recommend to sell
    else:
        return "HOLD", current_price #if criteria is not met hold the stock