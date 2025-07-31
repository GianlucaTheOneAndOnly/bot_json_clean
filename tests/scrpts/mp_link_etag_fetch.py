import json
import os
import sys
from typing import Dict, List, Optional

# --- Fix for ModuleNotFoundError ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# --- End Fix ---

from src.api.client import IcareApiClient, Server, initializer

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
    Runs a two-part test to determine how to link MPs and Transmitters.
    Test 1: Creates a new MP with a link.
    Test 2: Attempts to update an existing MP to add a link.
    """
    # --- Configuration ---
    CUSTOMER_DB = "csupport"
    FACTORY_NAME = "Test Jason"
    UPLOAD_PAYLOAD_PATH = "src/data/test_jason.json"

    # --- SHARED SETUP ---
    print("--- Running Shared Setup ---")
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
    server_asset_lookup = {asset['_id']: asset for asset in server_hierarchy_data}
    parent_to_transmitter_map = {
        asset['path'][-1]: asset['_id']
        for asset in server_hierarchy_data
        if asset.get('t') == 33554435 and asset.get('path')
    }
    print("--- Shared Setup Complete ---\n")

    # ==============================================================================
    # --- TEST 1: CREATE a new, linked MP to prove the creation method works ---
    # ==============================================================================
    print("="*60)
    print("--- STARTING TEST 1: CREATE a New, Linked Measurement Point ---")
    print("="*60)
    try:
        # Find a parent and transmitter to use for our test
        first_local_mp = next((asset for asset in local_upload_data if asset.get('t') == 16777218), None)
        if not first_local_mp:
            raise Exception("No local MP found in JSON to base the test on.")

        # Find the server ID of the parent component
        parent_component_upload_id = first_local_mp['upload_path'][-1]
        parent_component_server_id = id_map.get(parent_component_upload_id)
        if not parent_component_server_id:
            raise Exception("Could not find the server ID for the parent component.")

        # Find the transmitter that lives under that same parent
        transmitter_id_to_link = parent_to_transmitter_map.get(parent_component_server_id)
        if not transmitter_id_to_link:
            raise Exception(f"No transmitter found under parent component {parent_component_server_id}.")
        
        parent_component_asset = server_asset_lookup.get(parent_component_server_id)
        new_mp_path = parent_component_asset.get('path', []) + [parent_component_server_id]

        # Construct the payload for the new MP, mimicking the successful script
        new_mp_payload = {
            'name': "TEST - NEW MP (Created by Script)",
            't': 16777218,
            'path': new_mp_path,
            'optionals': {
                'speed': 1500,
                'transmitter': transmitter_id_to_link  # Set the link AT CREATION
            }
        }
        
        print(f"\nAttempting to create a new MP under parent {parent_component_server_id}...")
        print(f"Payload to be created: {json.dumps(new_mp_payload, indent=2)}")
        
        created_asset = client.create_asset(new_mp_payload)
        
        print("\n✅ ✅ ✅ TEST 1 SUCCESS! ✅ ✅ ✅")
        print("Successfully created a new MP with the transmitter link included:")
        print(json.dumps(created_asset, indent=2))

    except Exception as e:
        print("\n❌ ❌ ❌ TEST 1 FAILED! ❌ ❌ ❌")
        print(f"An error occurred during the creation test: {e}")

    # ===============================================================================
    # --- TEST 2: UPDATE existing MPs to confirm this method fails ---
    # ===============================================================================
    print("\n" + "="*60)
    print("--- STARTING TEST 2: UPDATE Existing Measurement Points ---")
    print("="*60)
    local_mps = [asset for asset in local_upload_data if asset.get('t') == 16777218]

    for local_mp in local_mps:
        mp_server_id = id_map.get(local_mp['upload_id'])
        if not mp_server_id: continue

        print(f"\nProcessing Existing MP: '{local_mp['name']}' (ID: {mp_server_id})")

        try:
            server_asset = client.get_asset(mp_server_id)
            payload_to_put = server_asset.copy()
            current_etag = payload_to_put.pop('_etag')

            mp_parent_id = payload_to_put.get('path', [])[-1] if payload_to_put.get('path') else None
            transmitter_to_link = parent_to_transmitter_map.get(mp_parent_id)
            
            if transmitter_to_link and payload_to_put.get('optionals', {}).get('transmitter') != transmitter_to_link:
                print(f"  Attempting to add link to transmitter {transmitter_to_link} via UPDATE...")
                if 'optionals' not in payload_to_put: payload_to_put['optionals'] = {}
                payload_to_put['optionals']['transmitter'] = transmitter_to_link
                
                # Remove read-only fields
                for key in ['_id', '_created', '_updated', '_links']:
                    payload_to_put.pop(key, None)
                
                # This call is expected to fail
                client.replace_asset(mp_server_id, current_etag, payload_to_put)
                print("  -> ✅ TEST 2: UPDATE unexpectedly SUCCEEDED.")
            else:
                print("  -> No update needed or no matching transmitter found.")

        except Exception as e:
            print(f"  -> ❌ TEST 2: UPDATE FAILED as expected. ❌")
            print(f"     Error: {e}")

if __name__ == '__main__':
    main()