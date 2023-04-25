from datetime import datetime
import pandas as pd
import numpy as np
from classes import Custom_df, Metrics_DF
import constants


def generate_transactions(order, df, totals, transType):
    transactions = []
    timestamp = order.pop('timestamp')
    for product, value in order.items():
        if transType == 'sale' and totals and totals[product] < value['units']: raise Exception(f'Error! Not enough {product} in stock')
        transactions.append([df['id'].max()+1+len(transactions), product, value['price'], value['units'], timestamp])
    return transactions

# taking relevant values from batch and sale and putting into one dictionary to represent the transaction
def get_trans_dict(sale, batch, gt):
    transaction = {k: v for k, v in batch.items() if k in ['wholesaleId', 'product', 'cost_per_unit']}
    transaction.update({'profit_per_unit': sale['price'] / sale['units'] - batch['cost_per_unit'],
                        'gross_per_unit': sale['price'] / sale['units'], 'timestamp': sale['timestamp']})
    if gt:
        result = [sale['price'] + batch['batch_profit'], sale['units'], batch['units'] - sale['units'], sale['price']]
    else: 
        result = [sale['price'] - (sale['price'] / sale['units'] * batch['units']), batch['units'], 0, sale['price'] / sale['units'] * batch['units']]
    transaction.update(dict(zip(['batch_profit', 'units_sold', 'units', 'order_gross'], result)))
    return transaction

'''
    - generate a transaction based on the current sale being iterated on
    - each sale must come from one or more "batches" i.e. wholesale purchases
    - so if there is enough in the batch we are looking at to make the sale, deduct from that batch and move on
    - else, we will need to split this sale across multiple batches. So subtract what you can from the current batch, and look at the
      leftover in the next iteration
'''
def log_transaction(batches, sales):
    enough_units = (batches.row['units'] >= sales.row['units'])
    transaction = get_trans_dict(sales.row, batches.row, enough_units)
    if enough_units:
        for item in ['batch_profit', 'units']:
            batches.row[item] = transaction[item]
        batches.append_to_df(batches.row, 'wholesaleId', 'temp_copy')
    else:
        sales.row['price'] -= transaction['order_gross']
        sales.row['units'] -= batches.row['units']
        sales.append_to_df(sales.row, 'id', 'df')
    return batches, transaction, sales

'''
    - take in a csv of the wholesale purchases and a csv of the retail sales
    - iterate through each sale and deduct from the corresponding wholesale purchases until there are no more sales
    - combine the wholesale and retail into one comprehensive csv, result.csv
'''
def generate_result(userID='testUser0'):
    sales = Custom_df(userID, f'retail')
    batches = Custom_df(userID, f'wholesale', True)
    while not sales.df.empty:
        sales.pop_row()
        batches.pop_row(sales.row['product'])
        batches, transaction, sales = log_transaction(batches, sales)
        batches.comp_trans(transaction)
    return batches.complete()

def generate_metrics(lookback=constants.ONE_WEEK,userID='testUser0',  lookbackUnit=constants.ONE_DAY):
    metrics = Metrics_DF(userID, lookback, lookbackUnit)
    return metrics.aggregate_retail_data()
