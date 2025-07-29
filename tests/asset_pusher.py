# File: push_asset_data.py

import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.client import initializer, Server
from requests.exceptions import HTTPError

# --- Configuration ---
# Define the complete desired state of the asset here.
# The script will either UPDATE an existing asset with this ID or CREATE a new one with this data.

ASSET_ID_TO_UPDATE_OR_CREATE = "686b92159fc5be4b90a98484"

ASSET_DATA = {
    "name": "12345",
    "t": "33554435",
    "path": [
    "5b2224d2e8b75738eb744c48",
    "686b87eb745ac0bb433756ba",
    "686b881525711d41b5a86449"
    ],
    "optionals": {
        "group": [],
        "mac": "helloworld",
        "serialnumber": "1234555",
        "oldpath": [],
        "transmitter_orientation": 0,
        "transmitter_mounting_method": 0,
        # You can add/change any other optional values here
        # For example, to update the offset:
        # "offset": 123.45 
    }
}

def _create_new_asset(client, asset_data):
    """
    Helper function to construct and send a request to create a new asset.
    """
    print("    - Proceeding to create a new asset with the specified data.")
    # The creation payload needs a parent ID, which is the last element of the path.
    if not asset_data.get("path"):
        print("\n--- CREATION FAILED: 'path' cannot be empty for a new asset. ---")
        return

    creation_payload = {
        "name": asset_data["name"],
        "t": asset_data["t"],
        "parent": asset_data["path"][-1], # Parent is the last item in the path
        "optionals": asset_data["optionals"]
    }

    print("\n[+] Preparing CREATE payload:")
    print(json.dumps(creation_payload, indent=4))
    
    print("\n[+] Sending CREATE request...")
    new_asset = client.create_asset(creation_payload)
    
    print("\n--- New Asset Created Successfully! ---")
    print("Server responded with new asset data:")
    print(json.dumps(new_asset, indent=4))


def main():
    """
    Main function to update an asset if it exists, or create it if it does not.
    """
    print("--- Starting Asset Update-or-Create Process ---")
    
    client = test_function_initializer(customer_db="csupport", server_region=Server.EU)
    if not client:
        print("\nClient initialization failed. Exiting.")
        return

    try:
        # --- STEP 1: Try to fetch the asset ---
        print(f"\n[1] Checking for existing asset: {ASSET_ID_TO_UPDATE_OR_CREATE}")
        existing_asset = client.get_asset(ASSET_ID_TO_UPDATE_OR_CREATE)
        print("    - Asset found. Preparing to update.")

        # --- ASSET EXISTS: PERFORM UPDATE ---
        current_etag = existing_asset.get('_etag')
        if not current_etag:
            raise ValueError("Found asset is missing an '_etag'. Cannot perform a safe update.")

        # Construct the update payload, ensuring the path is included to prevent orphaning.
        update_payload = {
            "name": ASSET_DATA["name"],
            "t": ASSET_DATA["t"],
            "path": existing_asset.get("path"), # IMPORTANT: Preserve the existing path
            "perm_inh" : existing_asset.get("perm_inh"),
            "optionals": ASSET_DATA["optionals"]
        }

        print("\n[2] Preparing UPDATE payload:")
        print(json.dumps(update_payload, indent=4))

        print("\n[3] Sending UPDATE request...")
        client.update_asset(ASSET_ID_TO_UPDATE_OR_CREATE, current_etag, update_payload)
        print("    - Update request sent successfully.")

        # --- STEP 4: VERIFY THE UPDATE ---
        print(f"\n[4] Verifying update by re-fetching asset...")
        try:
            verified_asset = client.get_asset(ASSET_ID_TO_UPDATE_OR_CREATE)
            print("\n--- Asset Update Verified! ---")
            print(json.dumps(verified_asset, indent=4))
        except HTTPError as e_verify:
            if e_verify.response.status_code == 403:
                # If verification fails with 403, it means the update made the asset inaccessible.
                # We will now create a new one as requested.
                print("    - Verification failed with 403 Forbidden. Asset is no longer accessible.")
                _create_new_asset(client, ASSET_DATA)
            else:
                # Re-raise other verification errors to be caught by the outer block.
                raise

    except HTTPError as e:
        if e.response.status_code == 404:
            # --- ASSET DOES NOT EXIST: PERFORM CREATE ---
            print("    - Asset not found initially.")
            _create_new_asset(client, ASSET_DATA)

        elif e.response.status_code == 412:
            print("\n--- UPDATE FAILED: Precondition Failed (Error 412) ---")
            print("This means the asset was modified by someone else after you fetched it.")
            print("Please re-run the script to try again with the latest version.")
        else:
            print(f"\n--- An HTTP error occurred ---")
            print(f"Status Code: {e.response.status_code}")
            print(f"Reason: {e.response.text}")
            
    except Exception as e:
        print(f"\n--- An unexpected error occurred ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
