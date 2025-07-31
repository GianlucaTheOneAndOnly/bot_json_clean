import json
import os
import sys
from typing import Dict, List, Optional

# --- Fix for ModuleNotFoundError ---
# This code dynamically adds the project's root directory to the Python path.
# It assumes this script is in tests/data_exploration, two levels down from the root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# --- End Fix ---

# --- Main Imports ---
# Use the initializer and Server enum from your actual client file
from src.api.client import IcareApiClient, Server, initializer

def get_factory_hierarchy_by_name(client: IcareApiClient, factory_name: str) -> List[Dict]:
    """
    Fetches the full hierarchy and filters it to return only a specific factory and its children.
    """
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
    """
    Creates a mapping from local upload_id to server _id by matching asset names and paths.

    Returns:
        A dictionary mapping {upload_id: _id}.
    """
    print("\nCreating ID map by comparing local file to server data...")
    
    # --- Step 1: Build lookup tables for both local and server data ---
    local_id_to_asset = {asset['upload_id']: asset for asset in local_data}
    server_id_to_asset = {asset['_id']: asset for asset in server_data}

    # --- Step 2: Create unique signatures for matching ---
    local_signatures = {}
    for upload_id, asset in local_id_to_asset.items():
        path_names = []
        parent_ids = asset.get('upload_path', [])
        for parent_upload_id in parent_ids:
            parent_asset = local_id_to_asset.get(parent_upload_id)
            if parent_asset:
                path_names.append(parent_asset['name'])
        
        signature = (asset['name'], tuple(path_names))
        local_signatures[signature] = upload_id

    server_signatures = {}
    for server_id, asset in server_id_to_asset.items():
        path_names = []
        parent_ids = asset.get('path', [])
        for parent_server_id in parent_ids:
            parent_asset = server_id_to_asset.get(parent_server_id)
            if parent_asset:
                path_names.append(parent_asset['name'])
        
        signature = (asset['name'], tuple(path_names))
        server_signatures[signature] = server_id

    # --- DEBUGGING: Print signatures to see the mismatch ---
    print("\n--- Debug: First 5 Local Signatures ---")
    for i, (sig, uid) in enumerate(local_signatures.items()):
        if i < 5:
            print(f"  {uid}: {sig}")

    print("\n--- Debug: First 5 Server Signatures ---")
    for i, (sig, sid) in enumerate(server_signatures.items()):
        if i < 5:
            print(f"  ID {sid[:5]}...: {sig}")
    # --- End Debugging ---

    # --- Step 3: Create the final mapping ---
    id_map = {}
    for signature, upload_id in local_signatures.items():
        if signature in server_signatures:
            server_id = server_signatures[signature]
            id_map[upload_id] = server_id
            
    print(f"\nSuccessfully created map for {len(id_map)} assets.")
    return id_map


def main():
    """
    Main execution block to perform the linking and task assignment.
    """
    # --- Configuration ---
    CUSTOMER_DB = "csupport"
    FACTORY_NAME = "Test Jason"
    UPLOAD_PAYLOAD_PATH = "src/data/test_jason.json"

    # --- Step 1: Initialization and Data Fetching ---
    client = initializer(customer_db=CUSTOMER_DB, server_region=Server.EU)
    if not client:
        return

    try:
        with open(UPLOAD_PAYLOAD_PATH, 'r') as f:
            local_upload_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The local file '{UPLOAD_PAYLOAD_PATH}' was not found.")
        return

    server_hierarchy_data = get_factory_hierarchy_by_name(client, FACTORY_NAME)
    if not server_hierarchy_data:
        return
        
    id_map = create_id_map(local_upload_data, server_hierarchy_data)
    if not id_map:
        print("\nID map is empty. Halting.")
        return
        
    server_asset_lookup = {asset['_id']: asset for asset in server_hierarchy_data}

    # --- Step 2: Fetch all existing preselections from the server ---
    print("\n--- Starting Step 2: Fetching Preselection Tasks ---")
    try:
        # Use the correct method to fetch all preselections
        all_preselections = client.get_preselections()
        # Create a map from the 'presid' to the preselection's actual '_id'
        task_map = {task.get('presid'): task.get('_id') for task in all_preselections}
        print(f"Successfully fetched {len(task_map)} preselections and created lookup map.")
    except Exception as e:
        print(f"ERROR: Could not fetch preselections from the server: {e}")
        return

    # --- Step 3: Link MPs and Assign Tasks using partial PATCH requests ---
    print("\n--- Starting Step 3: Linking and Task Assignment ---")
    
    local_mps = [asset for asset in local_upload_data if asset.get('t') == 16777218]
    
    for local_mp in local_mps:
        mp_upload_id = local_mp['upload_id']
        mp_server_id = id_map.get(mp_upload_id)
        if not mp_server_id:
            print(f"Warning: Could not find server ID for local MP '{local_mp['name']}' (upload_id: {mp_upload_id}). Skipping.")
            continue

        print(f"\nProcessing MP: '{local_mp['name']}' (ID: {mp_server_id})")
        
        server_asset = server_asset_lookup.get(mp_server_id)
        if not server_asset or '_etag' not in server_asset:
            print(f"Warning: Could not find server data or _etag for MP {mp_server_id}. Skipping.")
            continue
        
        current_etag = server_asset['_etag']
        
        try:
            # --- First PATCH: Link the transmitter ---
            transmitter_upload_id = local_mp.get('transmitter_upload_id')
            if transmitter_upload_id:
                transmitter_server_id = id_map.get(transmitter_upload_id)
                if transmitter_server_id:
                    # ** START OF FIX **
                    # 1. Get the existing 'optionals' object, or an empty dict if it doesn't exist.
                    optionals_payload = server_asset.get('optionals', {}).copy()
                    
                    # 2. Add/update the transmitter ID in our copy.
                    optionals_payload['transmitter'] = transmitter_server_id
                    
                    # 3. Create the final payload. The value of "optionals" is now the complete object.
                    link_payload = {"optionals": optionals_payload}
                    # ** END OF FIX **

                    print(f"  + Linking transmitter {transmitter_server_id}...")
                    updated_asset = client.update_asset(mp_server_id, current_etag, link_payload)
                    # IMPORTANT: Use the new ETag from the response for the next request
                    current_etag = updated_asset['_etag']
                    print(f"  -> Success.")
                else:
                    print(f"  - Warning: Could not find server ID for transmitter (upload_id: {transmitter_upload_id}).")

            # --- Second PATCH: Assign the preselection task (remains the same) ---
            local_presid = local_mp.get('preselection')
            if local_presid:
                task_server_id = task_map.get(local_presid)
                if task_server_id:
                    task_payload = {"preselection": task_server_id}
                    print(f"  + Assigning preselection task {task_server_id} (from presid {local_presid})...")
                    # Use the latest ETag for this second update
                    client.update_asset(mp_server_id, current_etag, task_payload)
                    print(f"  -> Success.")
                else:
                    print(f"  - Warning: Could not find a server preselection with presid '{local_presid}'.")

        except Exception as e:
            print(f"  - ERROR: An error occurred while updating MP {mp_server_id}: {e}")

if __name__ == '__main__':
    main()
