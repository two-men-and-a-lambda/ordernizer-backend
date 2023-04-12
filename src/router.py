import json
from endpoints import *

def lambda_handler(event, context):
    print('*'*100)
    print(event)
    print('!'*100)
    print(context)
    print('@'*100)
    path = event['path'][1:]
    try:
        body = json.loads(event['body'])
        print(body)
        print('&'*100)
    except:
        pass
    statusCode = 200
    if path == 'get_totals':
        result = get_totals()
    elif path == 'table':
        result = get_table_data()
    elif path == 'submit_inventory':
        result = submit_inventory(body)
    elif path == 'submit_order':
        result = submit_order(body)
    elif path == 'submit_sale':
        result = submit_sale(body)
    elif path == 'get_retail_output':
        result = get_csv('output/retail.csv')
    elif path == 'get_retail_input':
        result = get_csv('input/retail.csv')
    elif path == 'get_wholesale_output':
        result = get_csv('output/wholesale.csv')
    elif path == 'get_wholesale_input':
        result = get_csv('input/wholesale.csv')
    else:
        statusCode = 503
        result = f'{path} is not a valid endpoint'
    print('RESULT:')
    print(result)
    return { 
        'statusCode': statusCode,
        'body': json.dumps(result)
    }
