from datetime import datetime
import pandas as pd
import numpy as np
import logging


def pop_row(df):
    df_t = df.T
    row = df_t.pop(0).to_dict()
    df = df_t.T
    df = df.reset_index(drop=True)
    return df, row


def pop_row_two(df):
    df = df.reset_index(drop=True)
    row = df.iloc[0].to_dict()
    df = df.drop([0])
    df = df.reset_index(drop=True)
    return df, row


t = pd.read_csv('wholesale.csv').sort_values(by=['id'])

df, row = pop_row(t)
logging.info(df)
logging.info(row)
df, row = pop_row_two(t)
logging.info('*'*100)
logging.info(df)
logging.info(row)

# the_json = {
#     'filter': 'product',
#     # 'filter': 'month',
#     # 'filter': 'day',
#     # 'filter': 'batch',
#     # 'filter': 'cost_per_unit',
#     # 'filter': 'gross_per_unit',
#     # 'item': 'apples',
#     # 'item': 'bananas',
#     'start_time': '',
#     'end_time': '',
#     'search': 'profit_per_unit',
#     # 'search': 'gross_per_unit',
#     'metric': 'max',
#     # 'metric': 'min',
#     # 'metric': 'avg',
# }
# filter = the_json['filter']
# item = 'any item' if 'item' not in the_json.keys() else the_json['item']
# search = the_json['search']
# metric = the_json['metric']
# df = t
# if item in the_json.keys():
#     df = t[t[filter] == item]
# df = df.dropna(subset=[search])
# logging.info(df)
# if metric in ['min', 'max']:
#     if metric == 'max':
#         result = df[df[search] == df[search].max()]
#     elif metric == 'min':
#         result = df[df[search] == df[search].min()]
#     logging.info('\n', result)
#     logging.info(
#         f"\nThe {metric} {search} on a sale of {item} was transaction {result.index.values[0]} with a {search} of {result[search].values[0]}.  {result['units_sold'].values[0]} unit(s) were sold at ${result['gross_per_unit'].values[0]} after being purchased wholesale for ${result['cost_per_unit'].values[0]} as part of batch {result['wholesaleId'].values[0]}")
# elif metric == 'avg':
#     logging.info(
#         f"\nThe {metric} {search} on a sale of {item} was {df[search].mean()} with an average wholesale cost of {df['cost_per_unit'].mean()} and average sale price of {df['gross_per_unit'].mean()}")


# def pop_row(df):
#     df_t = df.T
#     row = df_t.pop(0).to_dict()
#     df = df_t.T
#     df = df.reset_index(drop=True)
#     return df, row


def pop_row_test(df):
    df = df.reset_index(drop=True)
    batch = df.iloc[0]
    batch = batch.to_dict()
    df = df.drop([0])
    return df, batch


# def pop_row_two(df):
#     df = df.reset_index(drop=True)
#     batch = df.iloc[0]
#     df = df.drop([0])
#     return df, batch


dataframe = pd.read_csv('test.csv')
logging.info('\n'*5, dataframe)
logging.info('*'*100)
dataframe = dataframe.rename(columns={'product': 'PRODUCT'})
logging.info(dataframe)
dataframe.to_csv('evan_a.csv')
dataframe['price'] = dataframe['price'] * 5 / 42
logging.info('*'*100)
logging.info(dataframe)
dataframe.to_csv('evan_b.csv')


def init():
    transactions = pd.read_csv('wholesale.csv').sort_values(by=['id'])
    transactions['cost_per_unit'] = transactions['price'] / \
        transactions['units']
    transactions['price'] *= -1
    transactions = transactions.rename(
        columns={'price': 'batch_profit', 'id': 'wholesaleId'})
    transactions['gross_per_unit'] = np.NaN
    dfs_per_product = {key: transactions[transactions['product'] == key]
                       for key in set(transactions['product'])}
    sales = pd.read_csv('retail.csv').sort_values(by=['id'])
    return transactions, dfs_per_product, sales


def pop_row(df):
    df = df.reset_index(drop=True)
    batch = df.iloc[0]
    batch = batch.to_dict()
    df = df.drop([0])
    return df, batch


def log_transaction(batch, sale, wholesale, sales):
    trans = {'wholesaleId': batch['wholesaleId'], 'product': batch['product'], 'cost_per_unit': batch['cost_per_unit'],
             'profit_per_unit': sale['price'] / sale['units'] - batch['cost_per_unit'], 'units_sold': sale['units'], 'timestamp': sale['timestamp'], 'gross_per_unit': sale['price'] / sale['units']}
    '''
        for the current sale we are looking at, if there is enough in the current batch then deduct from that
        batch and log the transaction
        else, deduct from the current batch as much as you can and log that as a transaction, then add the spillover as a remaining sale
        to the sales dataframe
    '''
    if batch['units'] >= sale['units']:
        batch_profit = sale['price'] + batch['batch_profit']
        units = batch['units'] - sale['units']
        order_gross = sale['price']
        batch['batch_profit'] = batch_profit
        batch['units'] = units
        wholesale = wholesale.append(batch, ignore_index=True).sort_values(
            by=['wholesaleId'])
    else:
        '''
            batch_profit = total price of sale - (price per unit sold * number of units remaining)
            example of above equation: I bought 10 apples for $50 ($5 per apple) and all I have in stock for the current batch is 4 apples
            batch_profit = $50 - ($5 * 4) = $30
        '''
        batch_profit = sale['price'] - \
            (sale['price'] / sale['units'] * batch['units'])
        units = 0
        order_gross = sale['price'] / \
            sale['units'] * batch['units']
        sale['price'] -= order_gross
        sale['units'] -= batch['units']
        # sales = pd.concat(
        #    [pd.DataFrame(sale, index=[0]), sales]).reset_index(drop=True)
        sales = sales.append(
            sale, ignore_index=True).sort_values(by=['id'])
    trans.update({'batch_profit': batch_profit,
                  'units': units, 'order_gross': order_gross})
    return wholesale, trans, sales


'''
    transactions: (dataframe) ledger of all transactions, initially just has wholesale
    dfs_per_product: (dictionary {string: dataframe}) each distinct product in transactions as the key and the sub-dataframe of transactions per each product as the values
    sales = (dataframe) all retail transactions
'''


def main():
    transactions, dfs_per_product, sales = init()
    # iterate through the transactions and sales starting from the oldest
    while not sales.empty:
        # get the oldest remaining sale and the oldest remaining "batch", aka wholesale purchase
        sales, sale = pop_row(sales)
        product = sale['product']
        wholesale, batch = pop_row(
            dfs_per_product[product])
        #####################################
        # wholesale, batch = pop_row(
        #     transactions[transactions['product'] == product])
        # transactions = transactions[transactions['product'] != product]
        ######################################
        # deduct the sale from the batch and record it in the transactions dataframe
        dfs_per_product[product], trans, sales = log_transaction(
            batch, sale, wholesale, sales)

        # transactions = pd.concat([wholesale, transactions])
        # transactions = transactions.sort_values(by=['timestamp'])
        # logging.info(transactions)
        # wholesale, trans, sales = log_transaction(
        #     batch, sale, wholesale, sales)
        # transactions = pd.concat(
        #     [transactions, wholesale], join='inner')
        # logging.info(transactions)
        transactions = transactions.append(trans, ignore_index=True)
    transactions = transactions.rename(columns={'units': 'units_remaining'})
    transactions = transactions[['wholesaleId', 'batch_profit', 'order_gross', 'product', 'cost_per_unit', 'gross_per_unit', 'profit_per_unit', 'units_sold',
                                 'units_remaining', 'timestamp']]
    logging.info('\n', transactions)


main()
'''
        batch_profit = total price of sale - (price per unit sold * number of units remaining)
        example of above equation: I bought 10 apples for $50 ($5 per apple) and all I have in stock for the current batch is 4 apples
        batch_profit = $50 - ($5 * 4) = $30
    '''


class Custom_df:
    def __init__(self):

    def pop_row():


def init():
    transactions = pd.read_csv('wholesale.csv').sort_values(by=['id'])
    transactions['cost_per_unit'] = transactions['price'] / \
        transactions['units']
    transactions['price'] *= -1
    transactions = transactions.rename(
        columns={'price': 'batch_profit', 'id': 'wholesaleId'})
    transactions['gross_per_unit'] = np.NaN
    sales = pd.read_csv('retail.csv').sort_values(by=['id'])
    return transactions, sales


def pop_row(df):
    df = df.reset_index(drop=True)
    batch = df.iloc[0]
    batch = batch.to_dict()
    df = df.drop([0])
    return df, batch


def get_trans_dict(sale, batch, gt):
    trans = {'wholesaleId': batch['wholesaleId'], 'product': batch['product'], 'cost_per_unit': batch['cost_per_unit'],
             'profit_per_unit': sale['price'] / sale['units'] - batch['cost_per_unit'], 'units_sold': sale['units'], 'timestamp': sale['timestamp'], 'gross_per_unit': sale['price'] / sale['units']}
    if gt:
        result = [sale['price'] + batch['batch_profit'],
                  batch['units'] - sale['units'], sale['price']]
    else:
        result = [sale['price'] - (sale['price'] / sale['units'] * batch['units']),
                  0, sale['price'] / sale['units'] * batch['units']]
    trans.update(dict(zip(['batch_profit', 'units', 'order_gross'], result)))
    return trans


def log_transaction(batch, sale, batches, sales):
    enough_units = (batch['units'] >= sale['units'])
    trans = get_trans_dict(sale, batch, enough_units)
    if enough_units:
        # if enough units in the batch to handle the sale, update the total profit for the batch and the units remaining, then append back to batches
        # as now the sale is over and this batch still has units remaining
        for item in ['batch_profit', 'units']:
            batch[item] = trans[item]
        batches = batches.append(batch, ignore_index=True).sort_values(
            by=['wholesaleId'])
    else:
        # else deduct as much as you can from the sale, then append the remaining back to sales
        # as this sale is not over and this batch has no units remaining
        sale['price'] -= trans['order_gross']
        sale['units'] -= batch['units']
        sales = sales.append(
            sale, ignore_index=True).sort_values(by=['id'])
    return batches, trans, sales


'''
    transactions: (dataframe) ledger of all transactions, initially just has wholesale
    dfs_per_product: (dictionary {string: dataframe}) each distinct product in transactions as the key and the sub-dataframe of transactions per each product as the values
    sales = (dataframe) all retail transactions
'''


def main():
    transactions, sales = init()
    # iterate through the transactions and sales starting from the oldest
    temp = transactions
    while not sales.empty:
        # get the oldest remaining sale and the oldest remaining "batch", aka wholesale purchase
        sales, sale = pop_row(sales)
        product = sale['product']
        temp_copy = temp[temp['product'] == product]
        temp_two = temp[temp['product'] != product]
        batches, batch = pop_row(
            temp_copy)
        # deduct the sale from the batch and record it in the transactions dataframe
        temp_copy, trans, sales = log_transaction(
            batch, sale, batches, sales)
        transactions = transactions.append(trans, ignore_index=True)
        temp = pd.concat([temp_copy, temp_two])
        temp = temp.sort_values(by=['timestamp'])
    transactions = transactions.rename(columns={'units': 'units_remaining'})
    transactions = transactions[['wholesaleId', 'batch_profit', 'order_gross', 'product', 'cost_per_unit', 'gross_per_unit', 'profit_per_unit', 'units_sold',
                                 'units_remaining', 'timestamp']]
    logging.info('\n', transactions)


main()

def get_trans_dict(sale, batch, gt):
    # taking relevant values from batch and sale and putting into one dictionary to represent the transaction
    batch_trans = {k: v for k, v in batch.items() if k in ['wholesaleId', 'product', 'cost_per_unit']}
    sale_trans = {k: v for k, v in sale.items() if k in ['units', 'timestamp']}
    transaction = batch_trans | sale_trans
    gross_per_unit = sale['price'] / sale['units']
    profit_per_unit = gross_per_unit - batch['cost_per_unit']
    order_gross = sale['price']
    if gt:
        batch_profit = order_gross + batch['batch_profit']
        units = batch['units'] - sale['units']
    else:
        batch_profit = order_gross - (order_gross / sale['units'] * batch['units'])
        units = 0
        order_gross = order_gross / sale['units'] * batch['units']
    
    transaction.update({'profit_per_unit': sale['price'] / sale['units'] - batch['cost_per_unit'],
                        'gross_per_unit': sale['price'] / sale['units'], 'units_sold': sale['units'], 'timestamp': sale['timestamp']})
    result = [sale['price'] + batch['batch_profit'], batch['units'] - sale['units'], sale['price']] if gt else [
        sale['price'] - (sale['price'] / sale['units'] * batch['units']), 0, sale['price'] / sale['units'] * batch['units']]
    transaction.update(
        dict(zip(['batch_profit', 'units', 'order_gross'], result)))
    return transaction


4,apples,150,10,'2023-01-29 20:45:06'