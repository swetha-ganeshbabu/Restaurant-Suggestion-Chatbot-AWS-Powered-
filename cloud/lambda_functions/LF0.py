import json
import boto3
import traceback
from datetime import datetime

lex_client = boto3.client('lexv2-runtime')
BOT_ID = 'Q4KSJPKSNE'
BOT_ALIAS_ID = 'TSTALIASID'
LOCALE_ID = 'en_US'

# DynamoDB for user state access
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('user-state')

# Query DynamoDB for user state
def query_dynamodb(userId):
    try:
        response = table.get_item(
            Key={
                'userId': userId
            }
        )
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving data from DynamoDB: {str(e)}")
        print(traceback.format_exc())
        return None

def invoke_lex(user_id, message, userId):
    try:
        response = lex_client.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId=userId,
            text=message
        )
        print("Lex response:", response)
        if response['messages']:
            return response['messages'][0]['content'], response['interpretations'][0]['intent']['name']
        else:
            return "Apologies, I couldn't quite catch that.", None
    except Exception as e:
        print(f"Issue while interacting with Lex: {str(e)}")
        print(traceback.format_exc())
        return "Sorry, I'm having some difficulty understanding you at the moment.", None

def lambda_handler(event, context):

    if 'messages' not in event or not event['messages']:
        return {
            'statusCode': 400,
            'body': json.dumps('No message content was found in the request.')
        }
    
    print("Processing request in Lambda function")
    userId = event['messages'][0]['unstructured']['userId']
    input_message = event['messages'][0]['unstructured']['text']
    print("Invoking Lex for user message processing")
    lex_response, intent_name = invoke_lex(userId, input_message, userId)
    print("Received response from Lex")
    
    user_state = query_dynamodb(userId)
    
    response_text = lex_response
    
    if user_state and intent_name == 'GreetingIntent':
        recent_recommendation = user_state.get('recentRecommendation')
        if recent_recommendation:
            response_text += f"\n\nBy the way, your last search suggests this option: {recent_recommendation}"
    
    response = {
        "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": userId,
                    "text": response_text,
                    "timestamp": datetime.now().isoformat()
                }
            }
        ]
    }
    
    return response
