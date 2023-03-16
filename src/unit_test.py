import pandas as pd
import requests
import boto3
from endpoints import *

def print_stuff(x, file, the_dict):
    print('*'*25,file,'*'*25)
    print('PASS' if x else 'FAILURE')
    for i, df in the_dict.items():
        print(f'{i.upper()}\n', df)

def test_api():
    bucket = boto3.resource(
        service_name='s3',
        region_name='us-east-1',
        aws_access_key_id='AKIA47ACC4ZGCT6JS5HC',
        aws_secret_access_key='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'
    ).Bucket('ordernizer-database-bucket')
    test_dict = {"submit_inventory": {"input": {"bananas": 20, "apples": 23, "timestamp": "2023-01-30 04:25:01"}, "expected": {"apples": 23, "bananas": 20}},
                 "submit_order": {"input": {"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 100}, "timestamp": "2023-01-30 04:25:01"}, "expected": {"apples": 123, "bananas": 40}},
                 "submit_sale": {"input": {"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 23}, "timestamp": "2023-01-30 04:25:01"}, "expected": {"apples": 133, "bananas": 35}}
    }
    for endpt, jsons in test_dict.items():
        print('*'*50,endpt,'*'*50)
        jsons['output'] = requests.post('https://f0nk1usvg2.execute-api.us-east-1.amazonaws.com/'+endpt, json=jsons['input']).json()
        print_stuff(int(jsons['expected'] == jsons['output']), 'JSON OBJECTS', jsons)
        for file in ['wholesale.csv', 'retail.csv']:
            dfs = {}
            for dir in ['input', 'output', f'test/{endpt}']:
                dfs[dir if dir in ['input', 'output'] else 'expected'] = pd.read_csv(bucket.Object(f'{dir}/{file}').get()['Body'], index_col=0)
            print_stuff(int(dfs['output'].equals(dfs['expected'])), file, dfs)
            
test_api()

