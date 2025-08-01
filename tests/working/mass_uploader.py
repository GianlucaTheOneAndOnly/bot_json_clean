import json
import os
import sys
import datetime
import math
import copy
from typing import Dict, List, Optional, Any

# --- Fix for ModuleNotFoundError ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# --- End Fix ---

from src.api.client import IcareApiClient, Server, initializer
# Import the task payload library
import src.data.task_payload_library as task_library

# --- Task Selection Logic ---
def selection_task_final(type: str, speed: Optional[int]) -> Optional[Any]:
    """
    Selects a task payload based on the given type and speed.
    """
    if speed is None:
        if type == 'vib': return task_library.vib_3000hz_6400
        if type == 'dna': return task_library.dna_2000hz_3200

    if type == 'temp':
        return task_library.temperature

    if speed is None: return None

    speed_map = {
        "very_low": (1, 80), "low": (81, 160), "low_mid": (161, 320),
        "mid": (321, 640), "high_mid": (641, 1000), "high": (1001, math.inf)
    }

    speed_key = next((key for key, (min_s, max_s) in speed_map.items() if min_s <= speed <= max_s), None)
    if not speed_key: return None

    payload_matrix = {
        'vib': {
            "very_low": task_library.vib_300hz_1600, "low": task_library.vib_600hz_1600,
            "low_mid": task_library.vib_1200hz_3200, "mid": task_library.vib_3000hz_6400,
            "high_mid": task_library.vib_5000hz_6400, "high": task_library.vib_10000hz_6400
        },
        'dna': {
            "very_low": task_library.dna_125hz_1600, "low": task_library.dna_250hz_1600,
            "low_mid": task_library.dna_500hz_1600, "mid": task_library.dna_1000hz_3200,
            "high_mid": task_library.dna_2000hz_3200,"high": task_library.dna_2000hz_3200,
        }
    }
    return payload_matrix.get(type, {}).get(speed_key)

# (Helper functions get_factory_hierarchy_by_name and create_id_map remain unchanged)
def get_factory_hierarchy_by_name(client: IcareApiClient, factory_name: str) -> List[Dict]:
    print(f"\nFetching full hierarchy to find factory: '{factory_name}'...")
    full_hierarchy = client.get_full_hierarchy()
    factory_node = next((asset for asset in full_hierarchy if asset.get('name') == factory_name), None)
    if not factory_node:
        print(f"Factory '{factory_name}' not found.")
        return []
    factory_id = factory_node['_id']
    print(f"Found factory '{factory_name}' with ID: {factory_id}. Filtering children...")
    factory_hierarchy = [asset for asset in full_hierarchy if asset['_id'] == factory_id or factory_id in asset.get('path', [])]
    return factory_hierarchy

def create_id_map(local_data: List[Dict], server_data: List[Dict]) -> Dict[int, str]:
    print("\nCreating ID map by comparing local file to server data...")
    local_id_to_asset = {asset['upload_id']: asset for asset in local_data}
    server_id_to_asset = {asset['_id']: asset for asset in server_data}
    local_signatures = {}
    for upload_id, asset in local_id_to_asset.items():
        path_names = [local_id_to_asset.get(p_uid, {}).get('name') for p_uid in asset.get('upload_path', [])]
        local_signatures[(asset['name'], tuple(filter(None, path_names)))] = upload_id
    server_signatures = {}
    for server_id, asset in server_id_to_asset.items():
        path_names = [server_id_to_asset.get(p_sid, {}).get('name') for p_sid in asset.get('path', [])]
        server_signatures[(asset['name'], tuple(filter(None, path_names)))] = server_id
    id_map = {up_id: server_signatures.get(sig) for sig, up_id in local_signatures.items() if server_signatures.get(sig)}
    print(f"Successfully created map for {len(id_map)} assets.")
    return id_map

def main():
    """
    Replaces unlinked MPs with new, fully configured ones (with transmitter and task links).
    """
    # --- Configuration ---
    CUSTOMER_DB = "csupport"
    FACTORY_NAME = "Lessines (CUP)"
    UPLOAD_PAYLOAD_PATH = "C:/Users/gianluca.carbone_ica/Desktop/Python codes/bot_json_clean/output.json"

    # --- SETUP ---
    client = initializer(customer_db=CUSTOMER_DB, server_region=Server.EU)
    if not client: return

    try:
        with open(UPLOAD_PAYLOAD_PATH, 'r') as f:
            local_upload_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{UPLOAD_PAYLOAD_PATH}' was not found.")
        return

    server_hierarchy_data = get_factory_hierarchy_by_name(client, FACTORY_NAME)
    if not server_hierarchy_data: return

    id_map = create_id_map(local_upload_data, server_hierarchy_data)
    parent_to_transmitter_map = {
        asset['path'][-1]: asset['_id']
        for asset in server_hierarchy_data
        if asset.get('t') == 33554435 and asset.get('path')
    }
    
    # --- CREATE-AND-REPLACE PROCESS ---
    print("\n--- Starting Create-Task-Delete Process for MPs ---")
    local_mps = [asset for asset in local_upload_data if asset.get('t') == 16777218]

    for local_mp in local_mps:
        old_mp_server_id = id_map.get(local_mp['upload_id'])
        if not old_mp_server_id: continue

        print(f"\nProcessing replacement for: '{local_mp['name']}' (Old ID: {old_mp_server_id})")
        
        newly_created_mp_id = None

        try:
            # --- DEBUG: Print initial speed from JSON ---
            initial_speed = initial_speed = local_mp.get('speed')
            print(f"  -> Reading initial MP data... Found speed in JSON: {initial_speed}")

            # 1. Get current info for the OLD MP
            old_mp_asset = client.get_asset(old_mp_server_id)
            old_mp_etag = old_mp_asset.get('_etag')
            old_mp_path = old_mp_asset.get('path')

            if not all([old_mp_etag, old_mp_path]):
                print("   - Could not retrieve essential data (ETag, path) for the old MP. Skipping.")
                continue

            parent_component_server_id = old_mp_path[-1]

            # 2. Find the transmitter to link to
            transmitter_id_to_link = parent_to_transmitter_map.get(parent_component_server_id)
            if not transmitter_id_to_link:
                print("   - No matching transmitter found under the same parent. Skipping.")
                continue

            # 3. CREATE the new MP
            print(f"  [Step 1/3] Creating new linked MP...")
            
            # Get speed from the nested 'optionals' dictionary and apply default if needed
            mp_speed = local_mp.get('speed', 1500)
            
            # --- DEBUG: Print final speed to be used ---
            print(f"  -> Final speed being used for new MP: {mp_speed}")

            new_mp_payload = {
                'name': local_mp['name'], 't': 16777218, 'path': old_mp_path,
                'optionals': {
                    'speed': mp_speed, # Use the determined speed
                    'transmitter': transmitter_id_to_link
                }
            }
            # Access 'dna' from the top level, as in your original code
            if local_mp.get('dna'): new_mp_payload['optionals']['dna'] = True
            
            created_asset = client.create_asset(new_mp_payload)
            newly_created_mp_id = created_asset['_id']
            print(f"  -> Success. New MP created with ID: {newly_created_mp_id}")

            # 4. CREATE the Task for the New MP using dynamic selection
            print(f"  [Step 2/3] Determining and assigning task to new MP...")
            
            # Determine type by accessing keys from the top level
            mp_type = 'vib'
            if local_mp.get('temp_only'): mp_type = 'temp'
            elif local_mp.get('dna'): mp_type = 'dna'

            # Call the selector with the correctly retrieved speed
            task_template = selection_task_final(type=mp_type, speed=mp_speed)

            if task_template:
                task_payload = copy.deepcopy(task_template)
                task_payload['asset'] = newly_created_mp_id
                task_payload['rule']['dtstart'] = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
                
                created_task = client.create_task(task_payload)
                task_name = task_payload.get('presname', 'N/A')
                print(f"  -> Success. Task '{task_name}' created with ID: {created_task['_id']}")
            else:
                print(f"  -> No applicable task found for type '{mp_type}' and speed '{mp_speed}'. Skipping task creation.")

            # 5. DELETE the old, unlinked MP
            print(f"  [Step 3/3] Deleting old unlinked MP ({old_mp_server_id})...")
            client.delete_asset(old_mp_server_id, old_mp_etag)
            print("  -> Success. Old MP deleted.")
            print("  ✅ Replacement complete.")

        except Exception as e:
            print(f"  ❌ ERROR: An error occurred during the replacement process.")
            print(f"     Details: {e}")
            if newly_created_mp_id:
                print(f"     !! ATTENTION: A new MP ({newly_created_mp_id}) was created but the old one was not deleted. Please check manually.")
            print("     Skipping this MP to be safe.")

    print("\n--- Create-Task-Delete Process Finished ---")

if __name__ == '__main__':
    main()