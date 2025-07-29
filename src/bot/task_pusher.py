import json
from api.client import initializer, Server
import datetime
import data.asset_library as asset_library
import data.task_payload_library as task
# --- Initialize the client ---
client = initializer(customer_db="csupport", server_region=Server.EU)

if client:
    # The ID of the asset you want to assign the task to
    asset_id = "686e508012321d2cc2406605" # Using the asset ID from the example

    # 1. Get the preselection data
    preselection = asset_library.default_preselection

    # 2. Get the current time as a Unix timestamp in milliseconds
    dtstart_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)

    payload = task.dna_2000_3200

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