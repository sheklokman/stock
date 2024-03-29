import numpy as np
import math
import pandas as pd
from stock_utils.bcolors import bcolors
from datetime import datetime, timedelta
from stock_utils import stock_utils
from telegram.telegram import telegram
import csv
import os
import yfinance as yf
import pandas_ta as ta

class simulator:

    def __init__(self, capital):
        self.capital = capital
        self.initial_capital = capital # keep a copy of the initial cpaital
        self.total_gain = 0
        self.buy_orders = {}
        self.history = []

        #create a pandas df to save history
        cols = ['stock', 'buy_price', 'n_shares', 'sell_price', 'net_gain', 'gain_perc', 'buy_date', 'sell_date', 'total_days_on_market', 'cup_len', 'handle_len', 'cup_depth', 'handle_depth', 'rrr', 'threshold']
        self.history_df = pd.DataFrame(columns = cols)

    def buy(self, stock, buy_price, buy_date, no_of_splits, buy_date_data):
        """
        function takes buy price and the number of shares and buy the stock
        """

        #calculate the procedure
        n_shares = self.buy_percentage(buy_price, 1/no_of_splits)
        self.capital = self.capital - buy_price * n_shares - (buy_price * n_shares * self.commission_fee)
        self.buy_orders[stock] = [buy_price, n_shares, buy_price * n_shares, buy_date, \
                                  buy_date_data['cup_len'] if 'cup_len' in buy_date_data.columns else None, \
                                  buy_date_data['handle_len'] if 'handle_len' in buy_date_data.columns else None, \
                                  buy_date_data['cup_depth'] if 'cup_depth' in buy_date_data.columns else None, \
                                  buy_date_data['handle_depth'] if 'handle_depth' in buy_date_data.columns else None, \
                                  buy_date_data['threshold'] if 'threshold' in  buy_date_data.columns else None, \
                                ]


        self.log(f'{bcolors.OKCYAN}Bought {stock} for {buy_price} with on the {buy_date.strftime("%Y-%m-%d")}. Account Balance: {self.capital}{bcolors.ENDC}')

    def sell(self, stock, sell_price, n_shares_sell, sell_date, buy_price, recommended_action, cup_len, handle_len, cup_depth, handle_depth, threshold):
        """
        function to sell stock given the stock name and number of shares
        """
        buy_price, n_shares, _, buy_date, _, _, _, _, _= self.buy_orders[stock]
        sell_amount = sell_price * (n_shares_sell)

        self.capital = self.capital + sell_amount - (sell_amount * self.commission_fee)

        if(n_shares - n_shares_sell) == 0: #if sold all
            self.history.append([stock, buy_price, n_shares, sell_price, buy_date, sell_date, cup_len, handle_len, cup_depth, handle_depth, threshold])
            del self.buy_orders[stock]
        else:
            n_shares = n_shares - n_shares_sell
            self.buy_orders[stock][1] = n_shares
            self.buy_orders[stock][2] = buy_price * n_shares
        
        profit = sell_price - buy_price 
               
        if profit > 0:
            self.log(f'{bcolors.OKGREEN}{recommended_action} - Sold {stock} for {sell_price} (Make profit {round(profit / buy_price * 100, 2)}%) on {sell_date.strftime("%Y-%m-%d")}. Account Balance: {self.capital}{bcolors.ENDC}')
        else:
            self.log(f'{bcolors.FAIL}{recommended_action} - Sold {stock} for {sell_price} (Lose money {round(profit / buy_price * 100, 2)}%) on {sell_date.strftime("%Y-%m-%d")}. Account Balance: {self.capital}{bcolors.ENDC}')

    def buy_percentage(self, buy_price, buy_perc = 1):
        """
        this function determines how much capital to spend on the stock and returns the number of shares
        """
        stock_expenditure = self.capital * buy_perc
        n_shares = math.floor(stock_expenditure / buy_price)
        return n_shares

    
    def print_bag(self, all_time_stocks_data, date):
        """
        print current stocks holding
        """
        print_bag = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<14} {:<10} {:<10} {:<10} {:<14} {:<10} {:<10}".format('DATE', 'STOCK', 'BUY PRICE', 'TODAY PRICE', 'GAIN%', 'SHARES', 'TODAY VALUE', 'DAYS_ON_MARKET', 'CUP LEN', 'HANDLE LEN', 'CUP DEPTH', 'HANDLE DEPTH', 'RRR', 'THRESHOLD')
        today_stock_value = 0.0
        for key, value in self.buy_orders.items():       
            try:    
                hist = all_time_stocks_data[key].loc[date.date():date.date()]
                close_price = hist['Close'][-1]
                days_on_market = stock_utils.get_market_days(value[3], date)
                cup_len = value[4]
                handle_len = value[5]
                cup_depth = np.round(value[6], 2)
                handle_depth = np.round(value[7], 2)
                threshold = value[8]
                rrr = np.round(cup_depth / handle_depth, 2)
                today_stock_value += value[1] * close_price
                if(close_price >= value[0]):                
                    print_bag += f'\n{bcolors.OKGREEN}{str(date.date()):<10} {key:<10} {np.round(value[0], 2):<10} {np.round(close_price, 2):<10}  {np.round((close_price - value[0]) / value[0] * 100, 2):<10} {value[1]:<10} {np.round(close_price * value[1], 2):<10} {days_on_market:<14} {cup_len:<10} {handle_len:<10} {cup_depth:<10} {handle_depth:<14} {rrr:<10} {threshold:<10}{bcolors.ENDC}'
                else:
                    print_bag += f'\n{bcolors.FAIL}{str(date.date()):<10} {key:<10} {np.round(value[0], 2):<10} {np.round(close_price, 2):<10}  {np.round((close_price - value[0]) / value[0] * 100, 2):<10} {value[1]:<10} {np.round(close_price * value[1], 2):<10} {days_on_market:<14} {cup_len:<10} {handle_len:<10} {cup_depth:<10} {handle_depth:<14} {rrr:<10} {threshold:<10}{bcolors.ENDC}'
            except:
                continue

        if self.capital + today_stock_value >= self.initial_capital:
            print_bag += f'\n{bcolors.OKGREEN}Today Capital: {np.round(self.capital + today_stock_value, 2)}{bcolors.ENDC}'
        else:
            print_bag += f'\n{bcolors.FAIL}Today Capital: {np.round(self.capital + today_stock_value, 2)}{bcolors.ENDC}'

        if(date.day == 28):
            self.log(print_bag, True)
        else: 
            self.log(print_bag, False)

    def create_summary(self, print_results = False):
        """
        create summary
        """
        if print_results:
            print("{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<12} {:<10} {:<10}".format('STOCK', 'BUY PRICE', 'SHARES', 'SELL PRICE', 'NET GAIN', 'CUP LEN', 'HANDLE LEN', 'CUP DEPTH', 'HANDLE DEPTH', 'RRR', 'THRESHOLD'))

        for values in self.history:
            stock = values[0]
            buy_price = values[1]
            n_shares = values[2]
            sell_price = values[3]
            buy_date = values[4]
            sell_date = values[5]
            cup_len = values[6]
            handle_len = values[7]
            cup_depth = values[8]
            handle_depth = values[9]
            threshold = values[10]

            net_gain = (sell_price - buy_price) * n_shares
            gain_perc = np.round((sell_price - buy_price) / buy_price * 100, 2)
            total_days_on_market = stock_utils.get_market_days(buy_date, sell_date)
            rrr = cup_depth / handle_depth
            
            self.total_gain += net_gain
            """
            self.history_df = self.history_df.append({'stock': stock, 'buy_price': buy_price, 'n_shares': n_shares, \
                'sell_price': sell_price, 'net_gain': net_gain, 'gain_perc': gain_perc, 'buy_date': buy_date, \
                'sell_date': sell_date, 'total_days_on_market': total_days_on_market, 'cup_len': cup_len, \
                'handle_len': handle_len, 'cup_depth': cup_depth, 'handle_depth': handle_depth, 'rrr': rrr}, ignore_index = True)
            """
            self.history_df = pd.concat([self.history_df, pd.DataFrame({
                'stock': [stock],
                'buy_price': [buy_price],
                'n_shares': [n_shares],
                'sell_price': [sell_price],
                'net_gain': [net_gain],
                'gain_perc': [gain_perc],
                'buy_date': [buy_date],
                'sell_date': [sell_date],
                'total_days_on_market': [total_days_on_market],
                'cup_len': [cup_len],
                'handle_len': [handle_len],
                'cup_depth': [cup_depth],
                'handle_depth': [handle_depth],
                'rrr': [rrr],
                'threshold': [threshold]
            })])

            if print_results:
                print("{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<12} {:<10} {:<10}" \
                      .format(stock, buy_price, n_shares, sell_price, np.round(net_gain, 2), cup_len, handle_len, np.round(cup_depth, 4), np.round(handle_depth, 4), np.round(rrr, 4), threshold))

    

    def print_summary(self):
        """
        prints the summary of results
        """
        self.create_summary(print_results= True)
        summary = f"""
Initial Balance: {self.initial_capital:.2f}
Final Balance: {(self.initial_capital + self.total_gain):.2f}
Total Gain: {self.total_gain:.2f}
P/L: {(self.total_gain / self.initial_capital) * 100:.2f} %
        """
        self.log(summary)

    def log(self, message, force_to_send_to_telegram = None):
        print(message)
        if self.send_to_telegram if force_to_send_to_telegram is None else force_to_send_to_telegram:
            t = telegram()
            message = message.replace(bcolors.HEADER, "")
            message = message.replace(bcolors.OKBLUE, "")
            message = message.replace(bcolors.OKCYAN, "")
            message = message.replace(bcolors.OKGREEN, "")
            message = message.replace(bcolors.WARNING, "")
            message = message.replace(bcolors.FAIL, "")
            message = message.replace(bcolors.ENDC, "")
            message = message.replace(bcolors.BOLD, "")
            message = message.replace(bcolors.UNDERLINE, "")
            t.send_message(message=message)

    def create_history_csv_header(self):
         with open(os.path.join(self.folder_dir, 'history_df.csv'), 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["STOCK", "BUY PRICE", "SHARES", "SELL PRICE", "NET GAIN", \
                             "GAIN%", "BUY DATE", "SELL DATE", "TOTAL DAYS ON MARKET", \
                                "CUP LEN", "HANDLE LEN", "CUP DEPTH", "HANDLE DEPTH", "RRR", "THRESHOLD"])

    def save_history(self, values):
        stock = values[0]
        buy_price = values[1]
        n_shares = values[2]
        sell_price = values[3]
        buy_date = values[4]
        sell_date = values[5]
        cup_len = values[6]
        handle_len = values[7]
        cup_depth = values[8]
        handle_depth = values[9]
        threshold = values[10]

        net_gain = (sell_price - buy_price) * n_shares
        gain_perc = np.round((sell_price - buy_price) / buy_price * 100, 2)
        total_days_on_market = stock_utils.get_market_days(buy_date, sell_date)
        rrr = cup_depth / handle_depth

        row = [stock, buy_price, n_shares, sell_price, net_gain, gain_perc, buy_date, sell_date, total_days_on_market, \
                cup_len, handle_len, cup_depth, handle_depth, rrr, threshold]

        with open(os.path.join(self.folder_dir, 'history_df.csv'), 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(row)