import json
import boto3
import random
import requests
import os
import traceback
import re

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')
restaurantTable = dynamodb.Table('yelp-restaurants')
userTable = dynamodb.Table('user-state')

class SQSQueue(object):
    def __init__(self, queue_url, region_name="us-east-1"):
        self.sqs = boto3.client("sqs", region_name=region_name)
        self.queue = queue_url

    def enqueue_message(self, msg):
        self.sqs.send_message(QueueUrl=self.queue, MessageBody=msg)

    def dequeue_message(self, wait_time_seconds=20):
        messages = self.sqs.receive_message(QueueUrl=self.queue, MaxNumberOfMessages=1, WaitTimeSeconds=wait_time_seconds)
        if "Messages" in messages:
            message = messages["Messages"][0]
            return message
        else:
            return None

    def delete_message(self, receipt_handle):
        try:
            self.sqs.delete_message(QueueUrl=self.queue, ReceiptHandle=receipt_handle)
            print("Successfully deleted message. ReceiptHandle:", receipt_handle)
        except:
            print("Failed to remove message:", receipt_handle)

def format_recommendation(restaurant, idx):
    return f"""
    ------------------------------------------
    Option {idx+1}:
    Name: {restaurant.get('Name', 'Unknown')}
    Cuisine: {restaurant.get('Cuisine', 'Unknown')}
    Address: {restaurant.get('Address', 'Unknown')}
    Rating: {restaurant.get('Rating', 'N/A')}
    ------------------------------------------
    """

def query_dynamodb(restaurant_id):
    try:
        response = restaurantTable.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('BusinessID').eq(restaurant_id)
        )
        items = response.get('Items', [])
        if items:
            return random.choice(items)
        else:
            print(f"No restaurant found with BusinessID {restaurant_id} in DynamoDB.")
            return None
    except Exception as e:
        print(f"Error retrieving data from DynamoDB: {str(e)}")
        return None

def get_restaurant_recommendations(cuisine):
    recommendations = []
    
    query = {
        "size": 5,
        "query": {
            "match": {
                "Cuisine": cuisine
            }
        }
    }
    
    es_host = os.environ['OS_URL']
    index = 'restaurants'
    url = f"{es_host}/{index}/_search"
    username = os.environ['OS_USERNAME']
    password = os.environ['OS_PASSWORD']
    headers = {'Content-Type': 'application/json'}
    
    response = requests.get(url, auth=(username, password), headers=headers, data=json.dumps(query))
    
    if response.status_code == 200:
        result = response.json()
        if result.get('hits', {}).get('total', {}).get('value', 0) > 0:
            for idx, hit in enumerate(result['hits']['hits']):
                business_id = hit['_source'].get('BusinessID')
                if business_id:
                    dynamo_result = query_dynamodb(business_id)
                    if dynamo_result:
                        recommendations.append(format_recommendation(dynamo_result, idx))
                else:
                    print(f"Warning: Missing BusinessID in Elasticsearch result {hit}")
        else:
            print("No relevant restaurant matches found in Elasticsearch.")
    else:
        print(f"Failed Elasticsearch query: {response.status_code}, {response.text}")
    
    return recommendations

def create_or_update_user_recommendation(user_id, recommendation):
    if not user_id:
        print("User ID not provided. Skipping storage of recommendation.")
        return
    
    try:
        response = userTable.get_item(Key={'userId': user_id})
        if 'Item' in response:
            userTable.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET recentRecommendation = :r',
                ExpressionAttributeValues={':r': recommendation},
                ReturnValues="UPDATED_NEW"
            )
            print("User recommendation successfully updated.")
        else:
            userTable.put_item(
                Item={'userId': user_id, 'recentRecommendation': recommendation}
            )
            print("New user recommendation entry created.")
    except Exception as e:
        print(f"Error during update or creation: {str(e)}")

def lambda_handler(event, context):
    print("Received Lex Event: ", json.dumps(event, indent=2))
    worker_queue = SQSQueue(os.environ['SQS_URL'], "us-east-1")
    result = worker_queue.dequeue_message()
    
    if result is None:
        print("No available jobs. Exiting...")
        return {
            'statusCode': 204,
            'body': json.dumps({"message": "No tasks available"})
        }
    
    try:
        print("Processing Job", type(result["Body"]), result["Body"])
        body = json.loads(result["Body"])
        user_email = body.get("Email")
        user_id = body.get("userId")
        receipt_handle = result["ReceiptHandle"]
        cuisine = body.get('Cuisine')
        
        recommendations = get_restaurant_recommendations(cuisine)
        
        if not recommendations:
            print("No recommendations found. Email will not be sent.")
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "No recommendations available"})
            }
        
        random_recommendation = random.choice(recommendations)
        random_recommendation = re.sub(r'-+|Option \d+:\s*', '', random_recommendation)
        create_or_update_user_recommendation(user_id, random_recommendation)
        
        recommendations_formatted = "\n".join(recommendations)
        print("Finalized Recommendations: ", recommendations_formatted)
        
        ses = boto3.client('ses', region_name='us-east-1')
        ses.send_email(
            Source='sm12155@nyu.edu',
            Destination={'ToAddresses': ['sm12155@nyu.edu']},
            Message={
                'Subject': {'Data': 'Recommended Restaurants'},
                'Body': {'Text': {'Data': recommendations_formatted}}
            }
        )
        
        worker_queue.delete_message(receipt_handle)
        
        return {'statusCode': 200, 'body': json.dumps(body)}
    
    except Exception as e:
        print("Error processing request: ", str(e))
        return {
            'statusCode': 400,
            'body': json.dumps({"error": str(e)}),
            'exception_traceback': traceback.format_exc()
        }
