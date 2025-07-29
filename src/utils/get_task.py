import json
from api.client import initializer, Server

# --- Initialize the client ---
client = initializer(customer_db="csupport", server_region=Server.EU)

if client:
    # --- IMPORTANT ---
    # PASTE THE ID OF THE ASSET YOU MANUALLY ADDED A PICTURE TO
    mp_id = "686e508012321d2cc2406605" 
    task_id = "686e79b71547e7de8874b833"
    
    try:
        print(f"Fetching data for asset: {mp_id}")
        asset_data = client.get_tasks(mp_id, task_id)
        
        # Print the full JSON data in a readable format
        print("\n--- Full Task JSON Data ---")
        print(json.dumps(asset_data, indent=2))
        print("--------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")