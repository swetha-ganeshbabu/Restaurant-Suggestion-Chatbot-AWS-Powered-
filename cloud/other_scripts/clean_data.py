import json
import pandas as pd

# Load collected data
with open("yelp_restaurants.json", "r") as f:
    restaurants = json.load(f)

# Convert to DataFrame for easy duplicate removal
df = pd.DataFrame(restaurants)

# Remove duplicates based on 'BusinessID'
df = df.drop_duplicates(subset="BusinessID", keep="first")

# Keep only the first 150 unique restaurants
df = df.head(150)

# Save cleaned data
df.to_json("yelp_restaurants_cleaned.json", orient="records", indent=4)

print(f"\n✅ Cleaning complete! Total restaurants stored: {len(df)}.")
print("🎉 Cleaned dataset saved to 'yelp_restaurants_cleaned.json'.")