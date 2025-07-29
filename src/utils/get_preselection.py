import json
from api.client import initializer, Server

# --- Initialize the client ---
client = initializer(customer_db="csupport", server_region=Server.EU)

if client:
    
    try:
        print(f"Fetching data for databaset: {client}")
        preselections = client.get_preselections(tach=False)
        
        # Print the full JSON data in a readable format
        print("\n--- Full Asset JSON Data ---")
        print(json.dumps(preselections, indent=2))
        print("--------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")