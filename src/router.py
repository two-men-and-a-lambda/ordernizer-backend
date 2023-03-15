import json
import pandas
from endpoints import *

def lambda_handler(event, context):
    print(event)
    print(context)
    path = event['path'][1:]
    if path == 'get_totals':
        result = get_totals()
    elif path == 'submit_inventory':
        result = submit_inventory(event['body'])
    elif path == 'submit_order':
        result = submit_order(event['body'])
    elif path == 'submit_sale':
        result = submit_sale(event['body'])
    else:
        return {  #         <---- RETURN THIS RIGHT AWAY 
        'statusCode': 503,
        'body': json.dumps(f'{path} is not a valid endpoint')
    }

    return {  #         <---- RETURN THIS RIGHT AWAY 
        'statusCode': 200,
        'body': json.dumps(result)
    }