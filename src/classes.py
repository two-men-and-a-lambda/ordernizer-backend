import pandas as pd
import numpy as np
import boto3
import os
import logging
from datetime import datetime, timedelta
import pytz
import constants


class Custom_df:
    def __init__(self, userID, csv, copy=False):
        env = os.getenv('ENV')
        logging.info('env: ' + str(env))
        if env=='local':
            filePath = f'./db/{userID}/{csv}.csv'
            self.df = pd.read_csv(filePath, sep=',').sort_values(by=['id'])

        else:
            s3 = boto3.client('s3')
            bucketPath = f'{userID}/{csv}.csv'
            logging.info(bucketPath)
            response = s3.get_object(Bucket='ordernizer-database-bucket', Key=bucketPath)
            self.df = pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])
            
        #self.df = pd.read_csv(csv).sort_values(by=['id'])
        if copy: self.batches_init(self.df)
        self.row = self.temp_copy = self.temp_two = None

    # to initialize the wholesale df, a few columns need to be added, and then a copy needs
    # to be made for later use
    def batches_init(self, df):
        df['cost_per_unit'] = df['price'] / df['units']
        df['price'] *= -1
        df = df.rename(columns={'price': 'batch_profit', 'id': 'wholesaleId'})
        df['gross_per_unit'] = np.NaN
        self.df = self.final_df = df

    def init_temps(self, product):
        self.temp_copy = self.df[self.df['product'] == product]
        self.temp_two = self.df[self.df['product'] != product]
        return 'temp_copy'

    # pop a row, set the results to self.row and self.<whichever df specified>
    def pop_row(self, product=None):
        df_str = 'df' if not product else self.init_temps(product)
        df = getattr(self, df_str).reset_index(drop=True)
        self.row = df.iloc[0].to_dict()
        setattr(self, df_str, df.drop([0]))

    def append_to_df(self, row, id=None, input_df=None):
        setattr(self, input_df, getattr(self, input_df).append(row, ignore_index=True).sort_values(by=[id]))

    # append the transaction to the final dataframe and then merge the temp df's back together
    def comp_trans(self, trans):
        self.append_to_df(trans, 'timestamp', 'final_df')
        self.df = pd.concat([self.temp_copy, self.temp_two]).sort_values(by=['timestamp'])

    # just reordering and renaming columns for the end
    def complete(self):
        final_df = self.final_df.rename(columns={'units': 'units_remaining'})
        self.final_df = final_df[['wholesaleId', 'batch_profit', 'order_gross', 'product', 'cost_per_unit',
                                  'gross_per_unit', 'profit_per_unit', 'units_sold', 'units_remaining', 'timestamp']]
        # self.final_df.to_csv('result.csv', index=False)
        logging.info(self.final_df)
        return self.final_df
    
    def __str__(self):
        return str(self.df)















class Metrics_DF:

    def __init__(self, userID, lookback, periodUnit):
        env = os.getenv('ENV')
        logging.info('env: ' + str(env))
        if env=='local':
            filePath = f'./db/{userID}/retail.csv'
            self.df = pd.read_csv(filePath, sep=',').sort_values(by=['id'])

        else:
            s3 = boto3.client('s3')
            bucketPath = f'{userID}/retail.csv'
            logging.info(bucketPath)
            response = s3.get_object(Bucket='ordernizer-database-bucket', Key=bucketPath)
            self.df = pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])

        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], utc=True)
        print(self.df)
        print(self.df.iloc[0]['timestamp'])

        utc = pytz.UTC

        self.reportEndDate = utc.localize(datetime.today())
        print(self.reportEndDate)
        self.reportEndDate = self.reportEndDate.replace(hour=0, minute=0, second=0, microsecond=0)
        print(self.reportEndDate)


        self.lookback = lookback
        self.periodDelta = self.unit_lookup(periodUnit)

        self.lookbackDate = self.get_lookback_date()

    def get_lookback_date(self):
        if self.lookback in constants.PRESETS:
            delta = self.unit_lookup(self.lookback)
            return self.reportEndDate - delta
        
        #TODO custom lookback date. Add logic later
        return self.lookback
    
    def unit_lookup(self, period):
        amount = int(period[0])
        unit = period[1]
        if unit == 'D':
            return timedelta(days=amount)
        elif unit == 'W':
            return timedelta(weeks=amount)
        elif unit == 'M':
            return timedelta(months=amount)
    
    def get_plot_points(self):
        plot_points = []
        rollingDate = self.reportEndDate
        

        while rollingDate > self.lookbackDate:
            plot_points.append(rollingDate)
            rollingDate -= self.periodDelta

        return plot_points

    def aggregate_retail_data(self):
        plotPoints = self.get_plot_points()
        result = {'totals':{}}
        for periodStartDate in plotPoints:
            periodEndDate = periodStartDate + self.periodDelta
            print(periodStartDate.strftime("%m/%d/%Y") + ' to ' + periodEndDate.strftime("%m/%d/%Y") + '\n')

            salesFrame = self.df[(self.df['timestamp'] > periodStartDate) & (self.df['timestamp'] <= periodEndDate)]
            print(salesFrame)
            print('\n\n')
            
            totalSalesFrame = salesFrame[['product', 'price', 'units']].groupby('product').agg({'product': 'max', 'units': 'sum', 'price':'sum'})
            totalSalesDict = totalSalesFrame.to_dict('index')
            print(totalSalesDict)

            averageSalesFrame = salesFrame[['product', 'price', 'units']].groupby('product').agg({'product': 'max', 'units': 'mean', 'price':'mean'})
            averageSalesDict = averageSalesFrame.to_dict('index')
            print(averageSalesDict)


            

    def timestampToDate(self, stamp):
        return datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
            
            








    
