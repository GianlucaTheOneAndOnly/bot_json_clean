import json
import datetime
import os
import sys
from typing import Dict, List


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.api.client import initializer, Server
import src.data.asset_library as asset_library
import src.data.task_payload_library as task

# --- Initialize the client ---
client = initializer(customer_db="csupport", server_region=Server.EU)

if client:
    # The ID of the asset you want to assign the task to
    asset_id = "688b7266431d247b51a25418" # Using the asset ID from the example

    # 1. Get the preselection data
    preselection = asset_library.default_preselection

    # 2. Get the current time as a Unix timestamp in milliseconds
    dtstart_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)

    payload = task.dna_2000hz_3200

    payload["asset"] = asset_id
    payload["rule"]["dtstart"] = dtstart_ms

    print("\nCreating new task with the correct payload...")
    print(json.dumps(payload, indent=2))
    
    try:
        # 4. Call the simple create_task function
        created_task = client.create_task(payload)
        
        print("\n--- SUCCESS! ---")
        print("Successfully created task:")
        print(json.dumps(created_task, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")