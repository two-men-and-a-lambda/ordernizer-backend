import pandas as pd
from io import StringIO
import boto3
from main import generate_result, generate_transactions, generate_metrics_df
import logging
import constants

def get_table_data(userID='testUser0'):
    
    df = generate_result(userID)
    logging.info('agg: ')
    logging.info(df)
    logging.info('\n\n\n\n')
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining', 'cost_per_unit', 'gross_per_unit']].groupby('wholesaleId').agg({'product': 'max', 'units_remaining': 'min', 'cost_per_unit':'max', 'gross_per_unit':'max'})
    logging.info('totals: ')
    logging.info(totals)
    logging.info('\n\n\n\n')
    totals_per_product = totals[['product', 'units_remaining']].groupby('product').sum()
    logging.info('totalspp: ')
    logging.info(totals_per_product)
    logging.info('\n\n\n\n')
    cost_per_product = totals[['product', 'cost_per_unit', 'gross_per_unit']].groupby('product').max()
    cost_per_product = cost_per_product.to_dict('index')

    logging.info('cpp: ')
    logging.info(cost_per_product)
    logging.info('\n\n\n\n')
    result = totals_per_product.to_dict('index')
    logging.info('result: ')
    logging.info(result)
    logging.info('\n\n\n\n')


    resultArray = []

    #-------------Temporary Hard Code-----------
    for product in result:
        result[product]['shipmentPrice'] = cost_per_product[product]['cost_per_unit']
        result[product]['salePrice'] = cost_per_product[product]['gross_per_unit']
        result[product]['pending'] = 0
        result[product]['shipment'] = 0
        result[product]['sale'] = 0
        result[product]['secondary'] = 0
        result[product]['ship_secondary'] = 0
        result[product]['product'] = product


        resultArray.append(result[product])
    #------------------------------------------
    
    return {'totals':resultArray}


def get_totals(userID='testUser0'):
    df = generate_result(userID)
    sold_out = list(set(df[df['units_remaining'] == 0]['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'product': 'max', 'units_remaining': 'min'})
    totals_per_product = totals[['product', 'units_remaining']].groupby('product').sum()
    return totals_per_product.to_dict()['units_remaining']

def append_rows_to_df(transactions, df):
    for transaction in transactions:
        df.loc[len(df)] = transaction
    return df

def get_file_as_pd(file):
    response = boto3.client('s3').get_object(Bucket='ordernizer-database-bucket', Key=file)
    return pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])

def get_csv_as_json(file):
    return get_file_as_pd(file).to_dict('records')

def put_file(df, file):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    boto3.resource('s3').Object('ordernizer-database-bucket', file).put(Body=csv_buffer.getvalue())

def submit_transaction(transactData, transType='order', totals=None, userID='testUser0'):
    if (transType == 'order'):
        file = 'wholesale'
    elif (transType == 'sale'):
        file = 'retail'

    input = get_file_as_pd(f'{userID}/{file}.csv')
    transactions = generate_transactions(transactData, input, totals, transType=transType)
    output = append_rows_to_df(transactions, input)
    put_file(output, f'{userID}/{file}.csv')
    # following two lines are just to assure for the unit test that the opposite file is being written to, otherwise calculations will be off
    # simply copying the input file into the output location
    #other_file = 'retail' if file == 'wholesale' else 'wholesale'
    #secondary = get_file(f"input/{other_file}.csv")
    #put_file(secondary, f'output/{other_file}.csv')

    return get_totals(userID)

def submit_inventory(new_totals, userID='testUser0'):
    totals = get_totals(userID=userID)
    timestamp = new_totals.pop('timestamp')

    ordersObj={}
    salesObj={}

    for product, units in new_totals.items():
        units_diff = totals[product] - units
        if (units_diff > 0):
            salesObj[product] = {'price': 0, 'units': units_diff}
        elif (units_diff < 0):
            ordersObj[product] = {'price': 0, 'units': units_diff * -1}
    
    if ordersObj:
        ordersObj['timestamp'] = timestamp
        submit_order(ordersObj, userID = userID, totals=totals)
    
    if salesObj:
        salesObj['timestamp'] = timestamp
        submit_sale(salesObj, userID = userID, totals=totals)

    return get_totals(userID)

def submit_sale(sale, userID='testUser0', totals=None):
    if totals is None:
        totals = get_totals(userID)

    return submit_transaction(sale, transType='sale', userID=userID, totals=totals)

def submit_order(sale, userID='testUser0', totals=None):
    if totals is None:
        totals = get_totals(userID)

    return submit_transaction(sale, transType='order', userID=userID, totals=totals)

def get_sales_chart_data(lookback=constants.ONE_WEEK,userID='testUser0',  lookbackUnit=constants.ONE_DAY):
    generate_metrics_df(userID, lookback, lookbackUnit)