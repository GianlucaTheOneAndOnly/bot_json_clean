import json
import os
import sys
import datetime
import math
import copy
from typing import Dict, List, Optional, Any
import unicodedata

# --- Fix for ModuleNotFoundError ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# --- End Fix ---

from src.api.client import IcareApiClient, Server, initializer
# Import the task payload library
import src.data.task_payload_library as task_library

# (Helper functions selection_task_final, get_factory_hierarchy_by_name, and create_id_map remain unchanged)
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

def get_factory_hierarchy_by_name(client: IcareApiClient, factory_name: str) -> List[Dict]:
    print(f"\nFetching full hierarchy to find factory: '{factory_name}'...")
    full_hierarchy = client.get_full_hierarchy()
    factory_nodes = [asset for asset in full_hierarchy if asset.get('name') == factory_name]
    if not factory_nodes:
        print(f"Factory '{factory_name}' not found.")
        return []
    factory_node = factory_nodes[0]
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
        norm_name = unicodedata.normalize('NFC', asset.get('name', ''))
        path_names = [unicodedata.normalize('NFC', local_id_to_asset.get(p_uid, {}).get('name', ''))
                      for p_uid in asset.get('upload_path', [])]
        signature = (norm_name, tuple(filter(None, path_names)))
        local_signatures[signature] = upload_id
    server_signatures = {}
    for server_id, asset in server_id_to_asset.items():
        norm_name = unicodedata.normalize('NFC', asset.get('name', ''))
        path_names = [unicodedata.normalize('NFC', server_id_to_asset.get(p_sid, {}).get('name', ''))
                      for p_sid in asset.get('path', [])]
        signature = (norm_name, tuple(filter(None, path_names)))
        server_signatures[signature] = server_id
    id_map = {up_id: server_signatures.get(sig) for sig, up_id in local_signatures.items() if server_signatures.get(sig)}
    print(f"Successfully created map for {len(id_map)} assets.")
    return id_map


def recreate_assets_with_new_firmware(client: IcareApiClient, server_data: List[Dict]):
    """
    Performs a deep recreation of Transmitters and Gateways to update firmware,
    with detailed error logging for channel recreation.
    """
    print("\n--- Starting Final Firmware Update Process (Detailed Logging) ---")

    FIRMWARE_MAP = {
        33554433: '00010405',  # Gateway
        33554435: '1700001d'   # Transmitter
    }
    
    assets_to_recreate = [asset for asset in server_data if asset.get('t') in FIRMWARE_MAP]
    if not assets_to_recreate:
        print("No Gateways or Transmitters found to update.")
        return

    for asset_summary in assets_to_recreate:
        asset_id = asset_summary.get('_id')
        asset_name = asset_summary.get('name', 'N/A')
        asset_type = "Gateway" if asset_summary.get('t') == 33554433 else "Transmitter"
        
        print(f"\nProcessing {asset_type}: '{asset_name}' (ID: {asset_id})")

        if asset_type == "Transmitter":
            try:
                # 1. Get info for each CHILD CHANNEL ASSET.
                print("  [1/6] Storing info for each child channel asset...")
                old_transmitter_full = client.get_asset(asset_id)
                stored_channel_payloads = []
                # The 'channels' key contains the full child asset objects.
                for channel_asset in old_transmitter_full.get('channels', []):
                    payload = copy.deepcopy(channel_asset)
                    for key in ['_id', '_etag', '_created', '_updated', '_links']:
                        payload.pop(key, None)
                    stored_channel_payloads.append(payload)
                
                # 2. Delete each CHILD CHANNEL ASSET.
                print(f"  [2/6] Deleting {len(stored_channel_payloads)} old channel asset(s)...")
                for channel_asset in old_transmitter_full.get('channels', []):
                    client.delete_asset(channel_asset['_id'], channel_asset['_etag'])
                print("  -> Old channel assets deleted.")

                # 3 & 4. Delete the PARENT TRANSMITTER ASSET.
                print("  [3-4/6] Deleting old transmitter asset...")
                etag_for_delete = client.get_asset(asset_id).get('_etag')
                client.delete_asset(asset_id, etag_for_delete)
                print("  -> Old transmitter asset deleted.")

                # 5. Create a new PARENT TRANSMITTER ASSET.
                print("  [5/6] Creating new transmitter asset...")
                new_transmitter_payload = copy.deepcopy(old_transmitter_full)
                for key in ['_id', '_etag', '_created', '_updated', '_links', 'channels']:
                    new_transmitter_payload.pop(key, None)
                
                if 'optionals' not in new_transmitter_payload:
                    new_transmitter_payload['optionals'] = {}
                new_transmitter_payload['optionals']['appfirmware'] = FIRMWARE_MAP[33554435]

                created_transmitter = client.create_asset(new_transmitter_payload)
                newly_created_transmitter_id = created_transmitter.get('_id')
                print(f"  -> New transmitter asset created with ID: {newly_created_transmitter_id}")

                # 6. Create a new CHILD CHANNEL ASSET for each stored channel.
                print("  [6/6] Recreating child channel assets...")
                new_transmitter_path = created_transmitter.get('path', [])
                new_channel_path = new_transmitter_path + [newly_created_transmitter_id]
                
                channels_recreated_count = 0
                for i, channel_payload in enumerate(stored_channel_payloads):
                    # This inner try/except logs errors for EACH channel asset.
                    try:
                        channel_payload['path'] = new_channel_path
                        print(f"    - Creating asset for channel '{channel_payload.get('name')}'...")
                        client.create_asset(channel_payload)
                        channels_recreated_count += 1
                        print(f"      ✅ Success.")
                    except Exception as e:
                        print(f"      ❌ FAILED to create asset for channel '{channel_payload.get('name', 'N/A')}'.")
                        print(f"        API Error: {e}")
                        print(f"        Failing Payload: {json.dumps(channel_payload, indent=4)}")

                if channels_recreated_count == len(stored_channel_payloads):
                    print("  -> All child channel assets recreated successfully.")
                    print(f"  ✅ Deep recreation for '{asset_name}' complete.")
                else:
                    print(f"  -> WARNING: Only {channels_recreated_count}/{len(stored_channel_payloads)} channel assets were recreated.")

            except Exception as e:
                print(f"  ❌ FATAL ERROR during deep recreation of '{asset_name}'.")
                print(f"    Details: {e}")
                print("    !! ATTENTION: Manual verification required.")

        else:  # Logic for Gateways
            # (Gateway logic remains the same)
            try:
                old_gateway_full = client.get_asset(asset_id)
                old_gateway_etag = old_gateway_full.get('_etag')
                new_gateway_payload = copy.deepcopy(old_gateway_full)
                for key in ['_id', '_etag', '_created', '_updated', '_links']:
                    new_gateway_payload.pop(key, None)
                if 'optionals' not in new_gateway_payload:
                    new_gateway_payload['optionals'] = {}
                new_gateway_payload['optionals']['appfirmware'] = FIRMWARE_MAP[33554433]
                print("  [1/2] Creating new gateway asset...")
                client.create_asset(new_gateway_payload)
                print("  [2/2] Deleting old gateway asset...")
                client.delete_asset(asset_id, old_gateway_etag)
                print(f"  ✅ Recreation for '{asset_name}' complete.")
            except Exception as e:
                print(f"  ❌ ERROR during gateway recreation for '{asset_name}'.")
                print(f"    Details: {e}")


def main():
    """
    Updates firmware by recreating assets, then replaces MPs.
    """
    # --- Configuration ---
    CUSTOMER_DB = "csupport"
    FACTORY_NAME = "Carambar Lutti FR Bondues" 
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

    # --- 1. FIRMWARE UPDATE via Deep Recreation ---
    recreate_assets_with_new_firmware(client, server_hierarchy_data)

    # --- CRITICAL REFRESH STEP ---
    print("\nRefreshing server data after asset recreation...")
    server_hierarchy_data = get_factory_hierarchy_by_name(client, FACTORY_NAME)
    if not server_hierarchy_data: 
        print("Could not refresh server data. Halting.")
        return

    # --- 2. CREATE-AND-REPLACE MP PROCESS ---
    id_map = create_id_map(local_upload_data, server_hierarchy_data)
    parent_to_transmitter_map = {
        asset['path'][-1]: asset['_id']
        for asset in server_hierarchy_data
        if asset.get('t') == 33554435 and asset.get('path')
    }
    
    print("\n--- Starting Create-Task-Delete Process for MPs ---")
    local_mps = [asset for asset in local_upload_data if asset.get('t') == 16777218]

    if not local_mps:
        print("No MPs found in local file to process.")

    for local_mp in local_mps:
        old_mp_server_id = id_map.get(local_mp['upload_id'])
        if not old_mp_server_id:
            continue

        #print(f"\nProcessing replacement for: '{local_mp['name']}' (Old ID: {old_mp_server_id})")
        
        newly_created_mp_id = None

        try:
            old_mp_asset = client.get_asset(old_mp_server_id)
            old_mp_etag = old_mp_asset.get('_etag')
            old_mp_path = old_mp_asset.get('path')

            if not all([old_mp_etag, old_mp_path]):
                #print("  - Could not retrieve essential data (ETag, path) for the old MP. Skipping.")
                continue

            parent_component_server_id = old_mp_path[-1]
            transmitter_id_to_link = parent_to_transmitter_map.get(parent_component_server_id)
            
            if not transmitter_id_to_link:
                print(f"  - No matching transmitter found under parent {parent_component_server_id}. Skipping.")
                continue

            #print(f"  [Step 1/3] Creating new linked MP...")
            mp_speed = local_mp.get('speed', 1500)
            
            new_mp_payload = {
                'name': local_mp['name'], 't': 16777218, 'path': old_mp_path,
                'optionals': { 'speed': mp_speed, 'transmitter': transmitter_id_to_link }
            }
            if local_mp.get('dna'): new_mp_payload['optionals']['dna'] = True
            
            created_asset = client.create_asset(new_mp_payload)
            newly_created_mp_id = created_asset['_id']
            #print(f"  -> Success. New MP created with ID: {newly_created_mp_id}")

            #print(f"  [Step 2/3] Determining and assigning task to new MP...")
            mp_type = 'vib'
            if local_mp.get('temp_only'): mp_type = 'temp'
            elif local_mp.get('dna'): mp_type = 'dna'

            task_template = selection_task_final(type=mp_type, speed=mp_speed)

            if task_template:
                task_payload = copy.deepcopy(task_template)
                task_payload['asset'] = newly_created_mp_id
                task_payload['rule']['dtstart'] = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
                created_task = client.create_task(task_payload)
                task_name = task_payload.get('presname', 'N/A')
                #print(f"  -> Success. Task '{task_name}' created with ID: {created_task['_id']}")
            else:
                print(f"  -> No applicable task found for type '{mp_type}' and speed '{mp_speed}'.")

            #print(f"  [Step 3/3] Deleting old unlinked MP ({old_mp_server_id})...")
            client.delete_asset(old_mp_server_id, old_mp_etag)
            #print("  -> Success. Old MP deleted.")
            #print("  ✅ Replacement complete.")

        except Exception as e:
            print(f"  ❌ ERROR: An error occurred during the replacement process.")
            print(f"    Details: {e}")
            if newly_created_mp_id:
                print(f"    !! ATTENTION: A new MP ({newly_created_mp_id}) was created but the old one was not deleted. Please check manually.")
            print("    Skipping this MP to be safe.")

    print("\n--- Create-Task-Delete Process Finished ---")

if __name__ == '__main__':
    main()