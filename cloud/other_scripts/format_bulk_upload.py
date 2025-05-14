import json

def create_bulk_json(input_file, output_file):
    """Convert cleaned restaurant JSON data to OpenSearch bulk format"""
    
    with open(input_file, "r") as f:
        restaurants = json.load(f)

    bulk_data = []
    
    for restaurant in restaurants:
        # Create the metadata line for bulk upload
        action = {
            "index": {
                "_id": restaurant["BusinessID"]
            }
        }
        bulk_data.append(json.dumps(action))
        
        # Add the actual restaurant data
        document = {
            "BusinessID": restaurant["BusinessID"],
            "Cuisine": restaurant["Cuisine"]
        }
        bulk_data.append(json.dumps(document))

    # Write formatted bulk data to output file
    with open(output_file, "w") as f:
        f.write("\n".join(bulk_data) + "\n")  # Ensure newline between records

if __name__ == "__main__":
    create_bulk_json("yelp_restaurants_cleaned.json", "restaurants_bulk_data.json")