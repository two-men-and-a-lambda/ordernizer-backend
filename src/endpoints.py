import pandas as pd
from io import StringIO
import boto3
from main import generate_result

'''
    - get the totals of each product in stock
    - uses generate_result() to combine wholesale and retail transactions into one comprehensive dataframe
    - then finds based on this dataframe what is currently in stock for each product
'''
def get_totals(retail='retail.csv', wholesale='wholesale.csv'):
    print('before gen result')
    df = generate_result(retail, wholesale)
    print('after gen result')
    sold_out_df = df[df['units_remaining'] == 0]
    sold_out = list(set(sold_out_df['wholesaleId']))
    in_stock = df[~df['wholesaleId'].isin(sold_out) ]
    totals = in_stock[['wholesaleId', 'product', 'units_remaining']].groupby('wholesaleId').agg({'product': 'max', 'units_remaining': 'min'})
    totals_per_product = totals[['product', 'units_remaining']].groupby('product').sum()
    totals_dict = totals_per_product.to_dict()['units_remaining']
    return totals_dict

'''
    - generates a list of lists
    - this list represents all transactions, which are to then be appended to a dataframe
'''
def generate_transactions(order, df, timestamp, totals=None):
    transactions = []
    for product, value in order.items():
        if totals and totals[product] < value['units']:
            message = f'Error! Not enough {product} in stock'
            print(message)
            raise Exception(message)
        transactions.append([df['id'].max()+1+len(transactions), product, value['price'], value['units'], timestamp])
    return transactions

def append_rows_to_df(transactions, df):
    for transaction in transactions:
        df.loc[len(df)] = transaction
    return df

'''
    - takes in a dictionary of inventory per product
    - based on this inventory, we look at what is currently supposed to be in stock based on the get_totals() function
    - and then find the discrepancies and log them as transactions with a price = 0
    ex: 
        - the get_totals() function returns that we have 8 apples
        - the store manager takes inventory and finds that they have 3 apples
        - submit_inventory({'apples': 3}) will record a sale of 5 apples for $0 and mark it as such in retail.csv
'''
def submit_inventory(new_totals, retail='retail.csv', wholesale='wholesale.csv'):
    totals = get_totals(retail, wholesale)
    timestamp = new_totals.pop('timestamp')
    diffs = {product: {'price': 0, 'units': totals[product] - units} for product, units in new_totals.items()} 
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='ordernizer-database-bucket', Key=retail)
    #sales = pd.read_csv(retail).sort_values(by=['id'])
    sales = pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])
    transactions = generate_transactions(diffs, sales, timestamp)
    sales = append_rows_to_df(transactions, sales)
    print('*'*100)
    print(sales)
    bucket = 'ordernizer-database-bucket' # already created on S3
    csv_buffer = StringIO()
    sales.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3')
    s3_resource.Object(bucket, 'test/retail.csv').put(Body=csv_buffer.getvalue())
    test_totals = get_totals('test/retail.csv', wholesale)
    return test_totals


'''
    - places an order to the wholesaler
    - adds the order to wholesale.csv
'''
def submit_order(order, wholesale='wholesale.csv'):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='ordernizer-database-bucket', Key=wholesale)
    #sales = pd.read_csv(retail).sort_values(by=['id'])
    batches = pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])
    timestamp = order.pop('timestamp')
    transactions = generate_transactions(order, batches, timestamp)
    batches = append_rows_to_df(transactions, batches)
    return batches

'''
    - logs a retail sale
    - if there is not enough inventory, returns an error and doesn't do anything
    - else, mark the transaction in retail.csv
'''
def submit_sale(sale, retail='retail.csv'):
    totals = get_totals()
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket='ordernizer-database-bucket', Key=retail)
    #sales = pd.read_csv(retail).sort_values(by=['id'])
    sales = pd.read_csv(response['Body'], sep=',').sort_values(by=['id'])
    timestamp = sale.pop('timestamp')
    transactions = generate_transactions(sale, sales, timestamp, totals)
    sales = append_rows_to_df(transactions, sales)
    return sales