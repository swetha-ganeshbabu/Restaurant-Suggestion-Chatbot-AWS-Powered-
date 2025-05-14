import json
import os
import boto3
import uuid 

# Initialize the SQS client
sqs = boto3.client('sqs')

QUEUE_URL = os.environ['SQS_QUEUE_URL']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        "sessionState": {
            "dialogAction": {
                "slotToElicit": slot_to_elicit,
                "type": "ElicitSlot"
            },
            "intent": {
                "name": intent_name,
                "slots": slots
            },
            "sessionAttributes": session_attributes
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ]
    }

def handle_greeting_intent(intent):
    return {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Fulfilled',
            'message': {
                'contentType': 'PlainText',
                'content': "Hi there! How can I assist you with finding a restaurant today?"
            }
        }
    }

def handle_thank_you_intent(intent):
    return {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Fulfilled',
            'message': {
                'contentType': 'PlainText',
                'content': "You're very welcome! Hope you have a great meal."
            }
        }
    }

def validate_slot(slot_name, slot_value):
    valid_locations = ['Manhattan', 'Nyc', 'New york city','Chicago','California']
    valid_cuisines = ['Chinese', 'Italian', 'Mexican']
    print(slot_name, slot_value,"inside validation")
    if slot_name == 'Location':
        return slot_value.capitalize() in valid_locations, f"Please select a valid location from: {', '.join(valid_locations)}."
    elif slot_name == 'Cuisine':
        return slot_value.capitalize() in valid_cuisines, f"The cuisine options available are: {', '.join(valid_cuisines)}. Please pick one."
    return True, ""

def handle_dining_suggestions_intent(intent, session_id):
    slots = intent['interpretations'][0]['intent']['slots']
    session_attributes = intent.get('sessionAttributes', {})
    intent_name = 'DiningSuggestionsIntent'
    
    required_slots = {
        'Location': 'Which city would you like to dine in?',
        'Cuisine': 'What kind of cuisine are you in the mood for?',
        'DiningTime': 'What time do you plan to have your meal?',
        'NumPeople': 'How many people will be joining you?',
        'Email': 'Can you provide your email so I can send the recommendations?'
    }
    
    for slot_name, prompt in required_slots.items():
        if slots.get(slot_name) is None or not slots[slot_name].get('value'):
            return elicit_slot(session_attributes, intent_name, slots, slot_name, prompt)
        
        slot_value = slots[slot_name]['value'].get('interpretedValue', slots[slot_name]['value'])
        print(slot_name, slot_value)
        if slot_name in ['Location', 'Cuisine']:
            is_valid, error_message = validate_slot(slot_name, slot_value)
            print(is_valid, error_message)
            if not is_valid:
                return elicit_slot(session_attributes, intent_name, slots, slot_name, error_message)
    
    print("iterations completed")
    
    location = slots['Location']['value'].get('interpretedValue', slots['Location']['value'])
    cuisine = slots['Cuisine']['value'].get('interpretedValue', slots['Cuisine']['value'])
    dining_time = slots['DiningTime']['value'].get('interpretedValue', slots['DiningTime']['value'])
    num_people = slots['NumPeople']['value'].get('interpretedValue', slots['NumPeople']['value'])
    email = slots['Email']['value'].get('interpretedValue', slots['Email']['value'])
    
    message = {
        'Location': location,
        'Cuisine': cuisine.capitalize(),
        'DiningTime': dining_time,
        'NumPeople': num_people,
        'Email': email, 
        'userId' : session_id
    }
    print(message)
    
    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message),
            MessageGroupId="DiningRequests",
            MessageDeduplicationId=str(uuid.uuid4())
        )
        print(f"Message successfully added to SQS: {message}")
    except Exception as e:
        print(f"Failed to send message to SQS: {str(e)}")
    
    print("Before thankyou")
    
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": f"Got it! I've noted your request for a {cuisine} restaurant in {location} for {num_people} people at {dining_time}. You'll receive an email with my suggestions at {email} soon."
            }
        ]
    }

def dispatch_handler(intent, session_id):
    intent_name = intent['interpretations'][0]['intent']['name']
    print("intent_called : "+intent_name)
    if intent_name == 'GreetingIntent':
        return handle_greeting_intent(intent)
    elif intent_name == 'ThankYouIntent':
        return handle_thank_you_intent(intent)
    elif intent_name == 'DiningSuggestionsIntent':
        return handle_dining_suggestions_intent(intent, session_id)
    else:
        return {
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': 'Failed',
                'message': {
                    'contentType': 'PlainText',
                    'content': "Sorry, I'm not sure how to assist with that request at the moment."
                }
            }
        }

def lambda_handler(event, context):
    print("Inside LF1")
    session_id = event.get('sessionId', 'default-session')
    print("sessionID "+str(session_id))
    return dispatch_handler(event, session_id)
