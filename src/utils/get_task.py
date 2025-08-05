import json
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.api.client import initializer, Server

# --- Initialize the client ---
client = initializer(customer_db="csupport", server_region=Server.EU)

if client:
    # --- IMPORTANT ---
    # PASTE THE ID OF THE ASSET YOU MANUALLY ADDED A PICTURE TO
    mp_id = "687a44441f2f4369915f5ed3" 
    task_id = "687a44451f2f4369915f5ed6"
    
    try:
        print(f"Fetching data for asset: {mp_id}")
        asset_data = client.get_tasks(mp_id, task_id)
        
        # Print the full JSON data in a readable format
        print("\n--- Full Task JSON Data ---")
        print(json.dumps(asset_data, indent=2))
        print("--------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")