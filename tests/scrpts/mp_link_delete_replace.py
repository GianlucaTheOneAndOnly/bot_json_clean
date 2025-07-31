import json
import os
import sys
from typing import Dict, List, Optional

# --- Fix for ModuleNotFoundError ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# --- End Fix ---

from src.api.client import IcareApiClient, Server, initializer

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
    print(f"Found {len(factory_hierarchy) - 1} children for factory '{factory_name}'.")
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
    Replaces unlinked MPs with new, correctly linked ones using a
    "Create-and-Delete" strategy.
    """
    # --- Configuration ---
    CUSTOMER_DB = "csupport"
    FACTORY_NAME = "Test Jason"
    UPLOAD_PAYLOAD_PATH = "src/data/test_jason.json"

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
    
    # Fetch preselections to link them during creation
    try:
        all_preselections = client.get_preselections()
        task_map = {task.get('presid'): task.get('_id') for task in all_preselections}
        print(f"\nSuccessfully fetched {len(task_map)} preselections for linking.")
    except Exception as e:
        print(f"ERROR: Could not fetch preselections: {e}")
        return

    # --- CREATE-AND-REPLACE PROCESS ---
    print("\n--- Starting Create-and-Replace Process for MPs ---")
    local_mps = [asset for asset in local_upload_data if asset.get('t') == 16777218]

    for local_mp in local_mps:
        old_mp_server_id = id_map.get(local_mp['upload_id'])
        if not old_mp_server_id:
            continue

        print(f"\nProcessing replacement for: '{local_mp['name']}' (Old ID: {old_mp_server_id})")

        try:
            # 1. Get current info for the OLD MP (we need its path and ETag to delete it)
            old_mp_asset = client.get_asset(old_mp_server_id)
            old_mp_etag = old_mp_asset.get('_etag')
            old_mp_path = old_mp_asset.get('path')

            if not all([old_mp_etag, old_mp_path]):
                print("  - Could not retrieve essential data (ETag, path) for the old MP. Skipping.")
                continue

            parent_component_server_id = old_mp_path[-1]

            # 2. Find the transmitter to link to
            transmitter_id_to_link = parent_to_transmitter_map.get(parent_component_server_id)
            if not transmitter_id_to_link:
                print("  - No matching transmitter found under the same parent. Skipping.")
                continue

            # 3. CREATE the new, correctly linked MP
            print(f"  [Step 1/2] Creating new linked MP with name '{local_mp['name']}'...")
            
            # Build the complete payload for the new MP
            new_mp_payload = {
                'name': local_mp['name'],
                't': 16777218,
                'path': old_mp_path,
                'optionals': {
                    'speed': local_mp.get('speed', 1500),
                    'transmitter': transmitter_id_to_link
                }
            }
            # Add other optional fields if they exist in the local data
            if local_mp.get('dna'):
                new_mp_payload['optionals']['dna'] = True
            if local_mp.get('temp_only'):
                new_mp_payload['optionals']['temp_only'] = True
            
            # Add the preselection link if it exists
            local_presid = local_mp.get('preselection')
            task_server_id = task_map.get(local_presid)
            if task_server_id:
                new_mp_payload['preselection'] = task_server_id

            created_asset = client.create_asset(new_mp_payload)
            print(f"  -> Success. New MP created with ID: {created_asset['_id']}")

            # 4. DELETE the old, unlinked MP
            print(f"  [Step 2/2] Deleting old unlinked MP ({old_mp_server_id})...")
            client.delete_asset(old_mp_server_id, old_mp_etag)
            print("  -> Success. Old MP deleted.")
            print("  ✅ Replacement complete.")

        except Exception as e:
            print(f"  ❌ ERROR: An error occurred during the replacement process.")
            print(f"     Details: {e}")
            print("     Skipping this MP to be safe.")

    print("\n--- Create-and-Replace Process Finished ---")

if __name__ == '__main__':
    main()