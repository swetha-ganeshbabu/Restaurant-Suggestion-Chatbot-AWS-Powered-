import boto3
import json
from decimal import Decimal

# AWS DynamoDB Table Name
TABLE_NAME = "yelp-restaurants"

# Initialize DynamoDB Client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# Load Cleaned Restaurant Data
with open("yelp_restaurants_cleaned.json", "r") as f:
    restaurants = json.load(f, parse_float=Decimal)  # Convert floats to Decimal

# Upload Each Restaurant Entry
for restaurant in restaurants:
    response = table.put_item(Item=restaurant)
    print(f"Uploaded: {restaurant['Name']}")

print("\n Data upload complete! All 150 restaurants added to DynamoDB.")