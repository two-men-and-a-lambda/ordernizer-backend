import pandas as pd
from io import StringIO
import boto3
from main import generate_result

def get_table_data(folder='input'):
    df = generate_result(folder)
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'wholesaleId': 'max', 'product': 'max', 'units_remaining': 'min'})
    resultArray = totals.to_dict('records')

    #-------------Temporary Hard Code-----------
    for row in resultArray:
        row['pending'] = 0
    #------------------------------------------
    
    return {'totals':resultArray}

def get_totals(folder='input'):
    df = generate_result(folder)
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'product': 'max', 'units_remaining': 'min'})
    
    result = totals.to_dict('records')
    return {'totals':result}

def generate_transactions(order, df, totals):
    transactions = []
    timestamp = order.pop('timestamp')
    for product, value in order.items():
        if totals and totals[product] < value['units']: raise Exception(f'Error! Not enough {product} in stock')
        transactions.append([df['id'].max()+1+len(transactions), product, value['price'], value['units'], timestamp])
    return transactions

def append_rows_to_df(transactions, df):
    for transaction in transactions:
        df.loc[len(df)] = transaction
    return df

def get_file(file):
    response = boto3.client('s3').get_object(Bucket='ordernizer-database-bucket', Key=file)
    return pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])

def put_file(df, file):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    boto3.resource('s3').Object('ordernizer-database-bucket', file).put(Body=csv_buffer.getvalue())

def submit_order(sale, file='wholesale', totals=None):
    input = get_file(f'input/{file}.csv')
    transactions = generate_transactions(sale, input, totals)
    output = append_rows_to_df(transactions, input)
    put_file(output, f'output/{file}.csv')
    # following two lines are just to assure for the unit test that the opposite file is being written to, otherwise calculations will be off
    # simply copying the input file into the output location
    other_file = 'retail' if file == 'wholesale' else 'wholesale'
    secondary = get_file(f"input/{other_file}.csv")
    put_file(secondary, f'output/{other_file}.csv')
    return get_totals('output')

def submit_inventory(new_totals):
    totals = get_totals()
    diffs = {product: {'price': 0, 'units': totals[product] - units} for product, units in new_totals.items() if product != 'timestamp'}
    diffs['timestamp'] = new_totals['timestamp']
    return submit_order(diffs, 'retail', totals)

def submit_sale(sale):
    totals = get_totals()
    return submit_order(sale, 'retail', totals)

get_totals()