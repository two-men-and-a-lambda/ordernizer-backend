import pandas as pd
import requests
import json
import boto3
from endpoints import *

def test():
    r = 'retail_test.csv'
    w = 'wholesale_test.csv'
    result = {'generate_result': [generate_result(r, w), pd.read_csv('generate_result.csv')], 'submit_sale': [submit_sale({'bananas': {'price': 10, 'units': 20}, 'apples': {'price': 30, 'units': 23}, 'timestamp': '2023-01-30 04:25:01'}, 'retail_test.csv'), pd.read_csv('submit_sale.csv')], 'submit_order': [submit_order({'bananas': {'price': 10, 'units': 20}, 'apples': {'price': 30, 'units': 100}, 'timestamp': '2023-01-30 04:25:01'}, 'wholesale_test.csv'), pd.read_csv('submit_order.csv')], 'submit_inventory': [submit_inventory({'bananas': 20, 'apples': 23, 'timestamp': '2023-01-30 04:25:01'}, 'retail_test.csv', 'wholesale_test.csv'), pd.read_csv('submit_inventory.csv')]}
    pass_fail_dict = {}
    for key, value in result.items():
        df1 = value[0]
        df2 = value[1]
        eq = df1.equals(df2)
        pass_fail_dict[key] = eq
        print('*'*50,key,'*'*50)
        if not eq:
            print('#'*50, 'FAIL', '#'*50)
        print('\nWHOLESALE:\n\n',pd.read_csv('wholesale_test.csv'))
        print('\nRETAIL:\n\n',pd.read_csv('retail_test.csv'))
        print('\nYOUR ANSWER:\n\n', df1)
        print('\nCORRECT ANSWER:\n\n', df2)
    print('\n\n')    
    for key, value in pass_fail_dict.items():
        print(key, ' '*(16-len(key)), 'PASS' if value else 'FAIL')
        

#test()

def test_api():
    s3 = boto3.resource(
        service_name='s3',
        region_name='us-east-1',
        aws_access_key_id='AKIA47ACC4ZGCT6JS5HC',
        aws_secret_access_key='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'
    )
    bucket = s3.Bucket('ordernizer-database-bucket')
    test_dict = {"submit_inventory": {"input": {"bananas": 20, "apples": 23, "timestamp": "2023-01-30 04:25:01"}, "output": {"apples": 23, "bananas": 20}}}
    #              "submit_order": {"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 100}, "timestamp": "2023-01-30 04:25:01"},
    #              "submit_sale": {"bananas": {"price": 10, "units": 20}, "apples": {"price": 30, "units": 23}, "timestamp": "2023-01-30 04:25:01"}
    # }
    result = {}
    for endpt, req_body in test_dict.items():
        print('*'*50,endpt,'*'*50)
        temp = []
        raw_resp = requests.post('https://f0nk1usvg2.execute-api.us-east-1.amazonaws.com/'+endpt, json=req_body['input'])
        resp = raw_resp.json()
        req_body['expected'] = resp
        x = int(resp == req_body['output'])
        temp.append(x)
        print('*'*25,'TOTALS', '*'*25)
        print('PASS' if x else 'FAILURE')
        for i in ['input', 'output', 'expected']:
            print(f'{i.upper()}\n', req_body[i])
        for file in ['wholesale.csv', 'retail.csv']:
            dfs = {}
            inp_obj = bucket.Object(f'{file}').get()
            dfs['input'] = pd.read_csv(inp_obj['Body'], index_col=0)
            out_obj = bucket.Object(f'test/{file}').get()
            dfs['output'] = pd.read_csv(out_obj['Body'], index_col=0)
            exp_obj = bucket.Object(f'test/{endpt}/{file}').get()
            dfs['expected'] = pd.read_csv(exp_obj['Body'], index_col=0)
            x = int(dfs['output'].equals(dfs['expected']))

            temp.append(x)
            print('*'*25,file,'*'*25)
            print('PASS' if x else 'FAILURE')
            for i, df in dfs.items():
                print(f'{i.upper()}\n', df)
test_api()