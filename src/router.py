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
        user = event["queryStringParameters"]["user"]
        print('user:' + user)
    except:
        statusCode = 503
        result = f'must include user in API request like /user?testUser0'
        return { 
        'statusCode': statusCode,
        'body': json.dumps(result)
    }

    try:
        body = json.loads(event['body'])
        print(body)
        print('&'*100)
    except:
        pass
    statusCode = 200
    if path == 'get_totals':
        result = get_totals(userID=user)
    elif path == 'table':
        result = get_table_data(userID=user)
    elif path == 'submit_inventory':
        result = submit_inventory(body, userID=user)
    elif path == 'submit_order':
        result = submit_order(body, userID=user)
    elif path == 'submit_sale':
        result = submit_order(body, userID=user)
    elif path == 'get_retail_output':
        result = get_csv_as_json('output/retail.csv')
    elif path == 'get_retail_input':
        result = get_csv_as_json('input/retail.csv')
    elif path == 'get_wholesale_output':
        result = get_csv_as_json('output/wholesale.csv')
    elif path == 'get_wholesale_input':
        result = get_csv_as_json('input/wholesale.csv')
    else:
        statusCode = 503
        result = f'{path} is not a valid endpoint'
    print('RESULT:')
    print(result)
    return { 
        'statusCode': statusCode,
        'body': json.dumps(result)
    }
