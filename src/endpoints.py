import pandas as pd
from io import StringIO
import boto3
from main import generate_result

def get_totals(folder='input'):
    df = generate_result(folder)
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'product': 'max', 'units_remaining': 'min'})
    totals_per_product = totals[['product', 'units_remaining']].groupby('product').sum()
    return totals_per_product.to_dict()['units_remaining']

def append_transactions_to_df(order, df, totals):
    timestamp = order.pop('timestamp')
    for product, value in order.items():
        if totals and totals[product] < value['units']: raise Exception(f'Error! Not enough {product} in stock')
        df.loc[len(df)] = [df['id'].max()+1, product, value['price'], value['units'], timestamp]
    return df

def read_csv_as_df(file):
    response = boto3.client('s3').get_object(Bucket='ordernizer-database-bucket', Key=file)
    return pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])

def write_df_to_csv(df, file):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    boto3.resource('s3').Object('ordernizer-database-bucket', file).put(Body=csv_buffer.getvalue())

def move_file(file_name, sale=None):
    input = read_csv_as_df(f"input/{file_name}.csv")
    if sale: df = append_transactions_to_df(sale, input, None if file_name == 'wholesale' else get_totals())
    write_df_to_csv(df, f'output/{file_name}.csv')

def submit_order(sale, file_name):
    other_file = 'retail' if file_name == 'wholesale' else 'wholesale'
    move_file(file_name, sale)
    move_file(other_file)
    return get_totals('output')

def get_diffs(new_totals):
    totals = get_totals()
    diffs = {product: {'price': 0, 'units': totals[product] - units} for product, units in new_totals.items() if product != 'timestamp'}
    diffs['timestamp'] = new_totals['timestamp']
    return diffs