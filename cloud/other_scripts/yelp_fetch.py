import requests
import json
from datetime import datetime

YELP_API_KEY = "pOje3jtDmKZxPJZSpmDKK7jQ-mc3vnr0wRl5jI7ACiB7Z49g7OMM0C5Dp6wFGfy0rtv0M97eRCgCgBjIfn1M4DyN5ZauBk-n5fEGrZ0h_0SCXH-k0aloZwQ899q4Z3Yx"

cuisines = ["Chinese", "Italian", "Mexican"]

headers = {"Authorization": f"Bearer {YELP_API_KEY}"}

all_restaurants = []

for cuisine in cuisines:
    print(f"\n🔍 Fetching {cuisine} restaurants...\n")
    
    params = {
        "term": f"{cuisine} restaurants",
        "location": "Manhattan, NY",
        "limit": 50  
    }

    url = "https://api.yelp.com/v3/businesses/search"
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    for restaurant in data.get("businesses", []):
        all_restaurants.append({
            "BusinessID": restaurant["id"],
            "Name": restaurant["name"],
            "Address": restaurant["location"].get("address1", "Unknown"),
            "City": restaurant["location"].get("city", "Unknown"),
            "Zip Code": restaurant["location"].get("zip_code", "Unknown"),
            "Rating": restaurant.get("rating", "N/A"),
            "Reviews": restaurant.get("review_count", "N/A"),
            "Cuisine": cuisine,
            "InsertedAtTimestamp": datetime.now().isoformat()
        })

    print(f"Collected {len(all_restaurants)} restaurants so far...")

# saving results to a JSON file
with open("yelp_restaurants.json", "w") as f:
    json.dump(all_restaurants, f, indent=4)

print("\n Data collection complete, saved to 'yelp_restaurants.json'.")