import pandas as pd
import numpy as np
import boto3


class Custom_df:
    def __init__(self, csv, copy=False):
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket='ordernizer-database-bucket', Key=csv)
        #self.df = pd.read_csv(csv).sort_values(by=['id'])
        self.df = pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])
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
        print(self.final_df)
        return self.final_df
