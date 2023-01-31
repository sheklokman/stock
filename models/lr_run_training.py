import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
plt.style.use('grayscale')

from scipy import linalg
import math
from datetime import datetime, timedelta
import warnings
# warnings.filterwarnings("ignore")

import time
import os
import sys
import pickle

# append path
current_dir = os.getcwd()
sys.path.append(current_dir)

from stock_utils import stock_utils
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import seaborn as sns

class LR_training:

    def __init__(self, model_veresion, threshold = 0.75, start_date = None, end_date = None, n = 10):

        self.model_version = model_veresion
        self.threshold = threshold

        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        
        # get stock tickers symobols
        current_dir = os.getcwd()
        hsi_tech = pd.read_csv(os.path.join(current_dir, 'stock_list/hsi/hsi_tech.csv'))['tickers'].tolist()
        hsi_main = pd.read_csv(os.path.join(current_dir, 'stock_list/hsi/hsi_main.csv'))['tickers'].tolist()
    
        stocks = list(np.unique(hsi_tech + hsi_main))        
        #stocks = pd.read_csv(os.path.join(current_dir, 'stock_list/hsi/hsi_all.csv'))['tickers'].tolist()
        self.stocks = list(np.unique(stocks))

        #main dataframe
        self.main_df = pd.DataFrame(columns = ['Volume', 'normalized_value', '3_reg', '5_reg', '10_reg', '20_reg', 'target'])

        # init models
        self.scalar = MinMaxScaler()
        self.lr = LogisticRegression()

        # run logistic regression
        self.fetch_data(start_date=start_date, end_date=end_date, n=n)
        #self.create_train_test()
        self.create_train_test()
        self.fit_model()
        self.confusion_matrix()
        self.save_model()


    def fetch_data(self, start_date, end_date, n):
        for stock in self.stocks:
            try:
                df = stock_utils.create_train_data(stock, start_date = start_date, end_date = end_date, n = n)
                self.main_df = pd.concat([self.main_df, df])
                print(f'Loaded {stock} stock history')
            except:
                pass
        print(f'{len(self.main_df)} samples were fetched')
    
    def create_train_test(self):
        self.main_df = self.main_df.sample(frac = 1, random_state = 3).reset_index(drop = True)
        self.main_df['target'] = self.main_df['target'].astype('category')

        y = self.main_df.pop('target').to_numpy()
        y = y.reshape(y.shape[0], 1)
        x = self.scalar.fit_transform(self.main_df)

        #test train split
        self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(x, y, \
            test_size = 0.05, random_state=50, shuffle= True)

        print('Created test and train data...')

    def fit_model(self):

        print('Training model...')
        self.lr.fit(self.train_x, self.train_y)

        # predict the test data
        self.predictions = self.lr.predict(self.test_x)
        self.score = self.lr.score(self.test_x, self.test_y)
        print(f'Logistic regression model score: {self.score}')

        #preds with threshold
        self.predictions_proba = self.lr._predict_proba_lr(self.test_x)
        self.predictions_proba_thresholded = self._threshold(self.predictions_proba, self.threshold)

    def confusion_matrix(self):
        cm = confusion_matrix(self.test_y, self.predictions)
        self.cmd = ConfusionMatrixDisplay(cm)

        cm_thresholded = confusion_matrix(self.test_y, self.predictions_proba_thresholded)
        self.cmd_thresholded = ConfusionMatrixDisplay(cm_thresholded)

    def _threshold(self, predictions, threshold):
        prob_thresholded = [0 if x > threshold else 1 for x in predictions[:, 0]]

        return np.array(prob_thresholded)

    def save_model(self):
        #save models
        saved_models_dir = os.path.join(os.getcwd(), 'saved_models')
        model_file = f'lr_{self.model_version}.sav'
        model_dir = os.path.join(saved_models_dir, model_file)
        pickle.dump(self.lr, open(model_dir, 'wb'))

        scaler_file = f'scaler_{self.model_version}.sav'
        scaler_dir = os.path.join(saved_models_dir, scaler_file)
        pickle.dump(self.scalar, open(scaler_dir, 'wb'))

        print(f'Saved the model and scaler in {saved_models_dir}')
        cm_path = os.path.join(os.getcwd(), 'results/Confusion Matrices')

        #save cms
        plt.figure()
        self.cmd.plot()
        plt.savefig(f'{cm_path}/cm_{self.model_version}.jpg')

        plt.figure()
        self.cmd_thresholded.plot()
        plt.savefig(f'{cm_path}/cm_thresholded_{self.model_version}.jpg')
        print(f'Figures saved in {cm_path}')


if __name__ == "__main__":
    # Train 4 years data
    end_date = datetime.now() - timedelta(days = 365)
    start_date = datetime.now() - timedelta(days=5*365)

    # Start training
    run_lr = LR_training('v2', threshold=0.75, start_date= start_date, end_date=end_date, n=10)


