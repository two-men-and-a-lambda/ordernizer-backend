import pandas as pd
from io import StringIO
import boto3
from main import generate_result

def get_table_data(folder='testUser0'):
    df = generate_result(folder)
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'wholesaleId': 'max', 'product': 'max', 'units_remaining': 'min'})
    resultArray = totals.to_dict('records')

    #-------------Temporary Hard Code-----------
    for row in resultArray:
        row['pending'] = 0
        row['shipment'] = 0
        row['sale'] = 0
        row['secondary'] = 0
        row['ship_secondary'] = 0
    #------------------------------------------
    
    return {'totals':resultArray}

def get_totals(folder='testUser0'):
    df = generate_result(folder)
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'product': 'max', 'units_remaining': 'min'})
    totals_per_product = totals[['product', 'units_remaining']].groupby('product').sum()
    return totals_per_product.to_dict()['units_remaining']

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

def get_csv(file):
    return get_file(file).to_dict('records')

def put_file(df, file):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    boto3.resource('s3').Object('ordernizer-database-bucket', file).put(Body=csv_buffer.getvalue())

def submit_order(sale, file='wholesale', totals=None, user='testUser0'):
    print(user)
    print(file)
    input = get_file(f'{user}/{file}.csv')
    transactions = generate_transactions(sale, input, totals)
    output = append_rows_to_df(transactions, input)
    put_file(output, f'{user}/{file}.csv')
    # following two lines are just to assure for the unit test that the opposite file is being written to, otherwise calculations will be off
    # simply copying the input file into the output location
    #other_file = 'retail' if file == 'wholesale' else 'wholesale'
    #secondary = get_file(f"input/{other_file}.csv")
    #put_file(secondary, f'output/{other_file}.csv')
    return get_totals(user)

def submit_inventory(new_totals, user='testUser0'):
    totals = get_totals(folder=user)
    timestamp = new_totals.pop('timestamp')

    ordersObj={}
    salesObj={}

    print(new_totals)
    print('\n\n')
    print(totals)

    for product, units in new_totals.items():
        units_diff = totals[product] - units
        print(str(product) + ': ' + str(units_diff))
        if (units_diff > 0):
            salesObj[product] = {'price': 0, 'units': units_diff}
        elif (units_diff < 0):
            ordersObj[product] = {'price': 0, 'units': units_diff * -1}
    
    if ordersObj:
        ordersObj['timestamp'] = timestamp
        submit_order(ordersObj, user = user, totals=totals)
    
    if salesObj:
        salesObj['timestamp'] = timestamp
        submit_sale(salesObj, user = user, totals=totals)

    return get_totals(user)

def submit_sale(sale, user='testUser0', totals=None):
    if totals is None:
        totals = get_totals(user)

    return submit_order(sale, file='retail', user=user, totals=totals)