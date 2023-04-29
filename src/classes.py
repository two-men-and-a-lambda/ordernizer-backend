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
        logging.info(self.df)
        logging.info(self.df.iloc[0]['timestamp'])

        utc = pytz.UTC

        self.reportEndDate = utc.localize(datetime.today())
        logging.info(self.reportEndDate)
        self.reportEndDate = self.reportEndDate.replace(hour=0, minute=0, second=0, microsecond=0)
        logging.info(self.reportEndDate)

        self.periodUnit = periodUnit


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
            #TODO lazy bastards dont have a months feature, maybe do this right at some point
            return timedelta(days=amount * 30)
    
    def get_plot_points(self):
        plot_points = []
        rollingDate = self.reportEndDate
        #we are calculating start dates, not end dates
        rollingDate -= self.periodDelta

        

        while rollingDate >= self.lookbackDate:
            if 'M' in self.periodUnit:
                #TODO this logic will not hold up for february
                resDate = (rollingDate + timedelta(days=30)).replace(month=rollingDate.month + 1,day=1)
                plot_points.append(resDate)
            else:
                plot_points.append(rollingDate)
            rollingDate -= self.periodDelta

            

        plot_points.reverse()
        return plot_points

    def aggregate_retail_data(self):

        #TODO maybe move this aggregation logic to javascript. 
        # Just send all sales data and sort is based on user input fields for reporting periods
        plotPoints = self.get_plot_points()

        productList = self.df["product"].values.tolist()
        productList = [*set(productList)]

        logging.info('productList:')
        logging.info(productList)
        
        salesTotals = {}
        revenueTotals = {}

        for product in productList:
            #initialize product data
            salesTotals[product] = {'series':[], 'name':product, 'sum': 0}
            revenueTotals[product] = {'series':[], 'name':product, 'sum': 0}
        #{
        # apples': 
        #   {series:[{value: 5, name: Monday},...], total: 585},
        # bananas':
        #   {series:[...], total: 226},
        #}
        

        for periodStartDate in plotPoints:
            periodEndDate = periodStartDate + self.periodDelta

            salesFrame = self.df[(self.df['timestamp'] > periodStartDate) & (self.df['timestamp'] <= periodEndDate)]
            logging.info('Data for period: ' + periodStartDate.strftime("%m/%d/%Y") + ' to ' + periodEndDate.strftime("%m/%d/%Y"))
            logging.info(salesFrame)
            logging.info('\n\n')
            
            totalSalesFrame = salesFrame[['product', 'price', 'units']].groupby('product').agg({'product': 'max', 'units': 'sum', 'price':'sum'})
            totalSalesDict = totalSalesFrame.to_dict('index')

            # add a blank data point that will get updated if there is real data for this period
            salesDataPoints = {}
            revenueDataPoints = {}

            for product in productList:
                salesDataPoints[product] = {'value':0, 'name':self.getXColumnLabel(periodStartDate)}
                revenueDataPoints[product] = {'value':0, 'name':self.getXColumnLabel(periodStartDate)}
            

            for product in totalSalesDict:
                units = totalSalesDict[product]['units']
                salesTotals[product]['sum'] += units
                salesDataPoints[product] = {'value':units, 'name':self.getXColumnLabel(periodStartDate)}

            #TODO more metrics
            #averageSalesFrame = salesFrame[['product', 'price', 'units']].groupby('product').agg({'product': 'max', 'units': 'mean', 'price':'mean'})
            #averageSalesDict = averageSalesFrame.to_dict('index')

            
            for product in totalSalesDict:
                price = totalSalesDict[product]['price']
                revenueTotals[product]['sum'] += price
                revenueDataPoints[product] = {'value':price, 'name':self.getXColumnLabel(periodStartDate)}
    
            for product in productList:
                salesTotals[product]['series'].append(salesDataPoints[product])
                revenueTotals[product]['series'].append(revenueDataPoints[product])
            
        salesTotalsJson = {}
        revenueTotalsJson = {}

        salesDataJson = []
        revenueDataJson = []

        for product in productList:
            totalSales = salesTotals[product].pop('sum')
            totalRevenue = revenueTotals[product].pop('sum')

            salesTotalsJson[product] = totalSales
            revenueTotalsJson[product] = totalRevenue

            salesDataJson.append(salesTotals[product])
            revenueDataJson.append(revenueTotals[product])

        resultDict = {
            'salesData': salesDataJson,
            'revenueData': revenueDataJson,
            'salesTotals': salesTotalsJson,
            'revenueTotals': revenueTotalsJson,
            'lookbackDate': self.lookbackDate.strftime('%m/%d/%Y'),
            'currentDate': self.reportEndDate.strftime('%m/%d/%Y'),
            'periodUnit': self.periodUnit
        }
        logging.info('\n\nFinal Chart data Result Json:')
        logging.info(resultDict)

        return resultDict


    def getXColumnLabel(self, periodStartDate: datetime):
        #TODO some logic "if units are months (march, april, may)"
        # if units are days "monday tuesday wednesday"
        # if units are weeks 7/4-7/11, 7/12-7/19, 7/20-7/27
        unit = self.periodUnit[1]
        if unit == 'D':
            return periodStartDate.strftime('%a %m/%d')
        elif unit == 'W':
            periodEndDate = periodStartDate + timedelta(weeks=1)
            endDate = periodEndDate.strftime('%m/%d')
            startDate = periodStartDate.strftime('%m/%d')
            return startDate + '-' + endDate
        elif unit == 'M':
            return periodStartDate.strftime('%B')

        

    def timestampToDate(self, stamp):
        return datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
            
            








    
