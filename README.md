# 🍽️ Restaurant Suggestion Chatbot (AWS-Powered)

A cloud-based dining concierge chatbot built with serverless architecture on AWS. The system intelligently interacts with users to collect dining preferences and recommends restaurants via email using data from Yelp, DynamoDB, and Elasticsearch.

## 🧠 Features

- 🤖 Conversational chatbot powered by Amazon Lex
- 🌐 API Gateway + Lambda integration for chat messaging
- 🏙️ Yelp-sourced restaurant data stored in DynamoDB
- 🔎 Fast filtering using Elasticsearch index
- 📩 Restaurant suggestions sent via AWS SES
- 🕰️ EventBridge/Cron-based automated queue processing
- 💬 Web-based chat frontend hosted on S3

## 🧰 Technologies Used

- **Amazon Lex** – Conversational AI
- **Amazon SQS** – Message queue for async processing
- **Amazon SES** – Email delivery
- **Amazon DynamoDB** – NoSQL restaurant data store
- **Amazon Elasticsearch** – Quick lookup by cuisine
- **Amazon Lambda** – Serverless compute
- **Amazon API Gateway** – RESTful API endpoint
- **Amazon S3** – Frontend hosting
- **CloudWatch/EventBridge** – Scheduler for LF2

## 🗂️ Project Structure
clooud/
├── frontend/                     # Static web interface
│   ├── chat.html
│   └── assets/
│       ├── css/                 # Styling (Bootstrap + Custom)
│       └── js/                  # Chat logic + AWS SDK/API Gateway SDK
│
├── json/                        # Yelp data (raw, cleaned, and bulk upload formats)
│   ├── restaurants_bulk_data.json
│   ├── yelp_restaurants.json
│   └── yelp_restaurants_cleaned.json
│
├── lambda_functions/           # Lambda scripts
│   ├── LF0.py                  # API Lambda: interfaces between frontend and Lex
│   ├── LF1.py                  # Lex Hook Lambda: handles intent logic
│   └── LF2.py                  # Queue worker Lambda: pulls from SQS, emails suggestions
│
├── other_scripts/              # Helper scripts
│   ├── clean_data.py
│   ├── yelp_fetch.py
│   ├── format_bulk_upload.py
│   └── upload_to_dynamodb.py

## 🛠️ Setup Instructions

1. 🧠 Set up Lex bot and intents
2. 🛜 Deploy API Gateway using Swagger
3. 🔗 Connect LF0 Lambda to API
4. 💬 Deploy LF1 for Lex fulfillment
5. 📦 Run Yelp scraper and upload to DynamoDB + Elasticsearch
6. 📥 Configure LF2 to poll SQS and send emails
7. 📅 Schedule LF2 via EventBridge
8. 🌍 Upload frontend to S3 bucket and test live

## 🚀 Deployment Overview

### 1. Frontend Hosting
- Static site hosted via **Amazon S3**
- Uses Bootstrap and the API Gateway SDK for chat integration

### 2. Amazon Lex Chatbot
- **GreetingIntent**: Welcomes the user
- **ThankYouIntent**: Responds politely
- **DiningSuggestionsIntent**: Collects:
  - Location
  - Cuisine
  - Date
  - Time
  - Number of people
  - Phone/Email

- Uses **LF1 Lambda hook** to validate and push user input to **SQS Queue (Q1)**

### 3. API Gateway + LF0 Lambda
- Acts as an API wrapper between frontend and Lex
- Enables CORS
- Uses Swagger for definition

### 4. Data Collection & Storage
- Yelp scraping using `yelp_fetch.py`
- Store data in:
  - **DynamoDB (yelp-restaurants)** for full info
  - **Elasticsearch** for indexed search

### 5. Email Suggestions via LF2 Lambda
- Triggered by EventBridge (every minute)
- Pulls from SQS → fetches from Elasticsearch → joins with DynamoDB → sends via SES

## 🧪 Example Conversation

User: Hello
Bot: Hi there, how can I help?
User: I need restaurant suggestions
Bot: Got it. What city?
User: Manhattan
Bot: What cuisine?
User: Japanese
Bot: For how many people?
User: 2
Bot: What time?
User: 7 pm
Bot: What’s your phone/email?
User: 123-456-7890
Bot: Great! Expect suggestions via email shortly.

📧 Sample Email:

Hello! Here are my Japanese restaurant suggestions for 2 people, today at 7 pm:
	1.	Sushi Nakazawa, 23 Commerce St
	2.	Jin Ramen, 3183 Broadway
	3.	Nikko, 1280 Amsterdam Ave

Enjoy your meal!

- Store user’s last search in DynamoDB
- When they return, greet them with a new suggestion based on past data
