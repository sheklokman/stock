import pandas_datareader as web
from datetime import date, datetime, time
import holidays
import numpy as np
import pandas as pd
from models.lr_inference import LR_sell, LR_predict
import warnings
from collections import OrderedDict
warnings.filterwarnings("ignore")
import os
from telegram.telegram import telegram



class stockfinder:

    def __init__(self, stocks_list, model, model_version, threshold = 0.75, sell_perc = 0.08, hold_till = 5, stop_perc = 0.08, no_of_recommendations = 3):
        self.stocks = stocks_list
        self.model = model
        self.model_version = model_version
        self.threshold = threshold
        self.sell_perc = sell_perc
        self.hold_till = hold_till
        self.stop_perc = stop_perc
        self.no_of_recommendations = no_of_recommendations

    def scan(self):
    
        model_recommended_stocks = {}
        for stock in self.stocks:
            try:
                prediction, prediction_thresholded, current_price = self.model(self.model_version, stock, '', '', self.threshold, data_type="realtime", hold_till = self.hold_till)

                if prediction_thresholded < 1:
                    model_recommended_stocks[stock] = (prediction, prediction_thresholded, current_price)
            except Exception as err:
                print(err)
                pass   
        def take_first(elem):
            return elem[1]  
        
        good_stocks = OrderedDict(sorted(model_recommended_stocks.items(), key = take_first, reverse = True))
  
        
        # Push the buying signal to Telegram channel
        # Get "no_of_recommendations" most good probabilities stocks
        t = telegram()
        if len(good_stocks) == 0:
            print(f'No recommendation at {datetime.now().strftime("%H:%M:%S")} by {self.model.__name__}_{self.model_version}')
            t.send_message(f'No recommendation at {datetime.now().strftime("%H:%M:%S")} by {self.model.__name__}_{self.model_version}')
        else:    
            for key in list(good_stocks)[0:self.no_of_recommendations]:
                stock = key
                current_price = good_stocks[key][2]
                sell_perc = self.sell_perc
                hold_till = self.hold_till
                stop_perc = self.stop_perc
                prediction_probability = good_stocks[key][0][0]

                
                t.send_formatted_message(model_name=f"{self.model.__name__}_{self.model_version}" , stock=stock, prediction_probability=prediction_probability, current_price=current_price, sell_perc=sell_perc, hold_till=hold_till, stop_perc=stop_perc)





if __name__ == "__main__":

    def is_time_between(begin_time, end_time, check_time=None):
        # If check time is not given, default to current Now time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    #Check if today is holiday
    hk_holidays = holidays.HK()
    today = date.today()
    if(today in hk_holidays):
        exit()

    # Check if now is between 09:45 and 16:00 (market time)
    if not is_time_between(time(9,30), time(16,00)):
        exit()

    current_dir = os.getcwd()    
    #hsi_tech = pd.read_csv(os.path.join(current_dir, 'stock_list/hsi/hsi_tech.csv'))['tickers'].tolist()
    #hsi_main = pd.read_csv(os.path.join(current_dir, 'stock_list/hsi/hsi_main.csv'))['tickers'].tolist()
    #stocks = list(np.unique(hsi_tech + hsi_main))       
    #stocks = pd.read_csv(os.path.join(current_dir, 'stock_list/hsi/hsi_all.csv'))['tickers'].tolist()

    stocks = []
    for stock_cat in ['hsi_integrated_large']: #'hsi_integrated_large', 'hsi_integrated_medium',
        stocks = stocks + pd.read_csv(os.path.join(current_dir, f'stock_list/hsi/{stock_cat}.csv'))['tickers'].tolist()
    stocks = list(np.unique(stocks)) 

    
    stockfinder(stocks, LR_predict, 'v1', threshold = 0.95, sell_perc = 0.1, hold_till= 10, stop_perc = 0.05, no_of_recommendations = 3).scan()
    stockfinder(stocks, LR_predict, 'v2', threshold = 0.95, sell_perc = 0.1, hold_till= 10, stop_perc = 0.05, no_of_recommendations = 3).scan()


