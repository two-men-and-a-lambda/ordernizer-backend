import pandas as pd
import requests
import boto3
import os
from endpoints import *
from classes import Custom_df
import logging
import datetime

def print_stuff(x, file, the_dict):
    logging.info('*'*25,file,'*'*25)
    logging.info('PASS' if x else 'FAILURE')
    for i, df in the_dict.items():
        logging.info(f'{i.upper()}\n', df)

def test_api():
    bucket = boto3.resource(
        service_name='s3',
        region_name='us-east-1',
        utest_aws_access_key_id=os.getenv('utest_aws_access_key_id'),
        utest_aws_secret_access_key=os.getenv('utest_aws_secret_access_key')
    ).Bucket('ordernizer-database-bucket')
    test_dict = {"submit_inventory": {"input": {"bananas": 20, "apples": 23, "timestamp": "2023-01-30 04:25:01"}, "expected": {"apples": 23, "bananas": 20}},
                 "submit_transaction": {"input": {"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 100}, "timestamp": "2023-01-30 04:25:01"}, "expected": {"apples": 156, "bananas": 55}},
                 "submit_sale": {"input": {"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 23}, "timestamp": "2023-01-30 04:25:01"}, "expected": {"apples": 33, "bananas": 15}}
    }
    for endpt, jsons in test_dict.items():
        logging.info('*'*50,endpt,'*'*50)
        jsons['output'] = requests.post('https://f0nk1usvg2.execute-api.us-east-1.amazonaws.com/'+endpt, json=jsons['input']).json()
        print_stuff(int(jsons['expected'] == jsons['output']), 'JSON OBJECTS', jsons)
        for file in ['wholesale.csv', 'retail.csv']:
            dfs = {}
            for dir in ['input', 'output', f'test/{endpt}']:
                dfs[dir if dir in ['input', 'output'] else 'expected'] = pd.read_csv(bucket.Object(f'{dir}/{file}').get()['Body'], index_col=0)
            print_stuff(int(dfs['output'].equals(dfs['expected'])), file, dfs)
            
#test_api()

#a = get_totals(folder='testUser0')
#logging.info(a)

#b = get_table_data(folder='testUser0')
#logging.info(b)

#b = submit_inventory({"bananas":34,"apples":88,"timestamp":"2023-04-22T16:15:18.886Z"},userID='testUser0',)
#logging.info(b)

#d = submit_sale({"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 100}, "timestamp": "2023-01-30 04:25:01"}, user='testUser0')
#logging.info(d)

#a = Custom_df('testUser0', 'wholesale', True)

logging.basicConfig(level=logging.INFO)
#a=get_table_data()
a=get_sales_chart_data()
#a = get_table_data('testUser0')
logging.info(a)
