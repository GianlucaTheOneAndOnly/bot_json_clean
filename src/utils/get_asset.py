import json
import sys
import os
from typing import List, Dict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.api.client import initializer, Server

# --- Initialize the client ---
client = initializer(customer_db="csupport", server_region=Server.EU)

if client:
    # --- IMPORTANT ---
    # PASTE THE ID OF THE ASSET YOU MANUALLY ADDED A PICTURE TO
    asset_id = "688b5a1d391d0c94d60e7a40" 
    
    try:
        print(f"Fetching data for asset: {asset_id}")
        asset_data = client.get_asset(asset_id)
        
        # Print the full JSON data in a readable format
        print("\n--- Full Asset JSON Data ---")
        print(json.dumps(asset_data, indent=2))
        print("--------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")