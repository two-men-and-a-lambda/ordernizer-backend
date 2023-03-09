import json
import pandas

def lambda_handler(event, context):
    print(event)
    print(context)
    return {  #         <---- RETURN THIS RIGHT AWAY 
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda! Ben your penis is small')
    }

