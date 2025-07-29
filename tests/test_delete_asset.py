# File: asset_delete.py

import json
import sys
import os
from requests.exceptions import HTTPError

# Add the parent directory to the path to allow importing the 'api' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.client import initializer, Server

# --- Configuration ---
# Specify the ID of the asset you want to delete.
ASSET_ID_TO_DELETE = "686e5080999cef7296cb04e2" # <--- CHANGE THIS ID

def main():
    """
    Main function to find and safely delete a specific asset.
    """
    print("--- Starting Asset Deletion Process ---")
    
    # Initialize the API client
    client = initializer(customer_db="csupport", server_region=Server.EU)
    if not client:
        print("\nClient initialization failed. Exiting.")
        return

    try:
        # --- STEP 1: Fetch the asset to get its current ETag ---
        print(f"\n[1] Fetching asset to be deleted: {ASSET_ID_TO_DELETE}")
        asset_to_delete = client.get_asset(ASSET_ID_TO_DELETE)
        
        # The ETag is required for a safe deletion operation
        current_etag = asset_to_delete.get('_etag')
        if not current_etag:
            raise ValueError("Asset found but is missing an '_etag'. Cannot perform a safe deletion.")
            
        print(f"    - Asset found. Current version (ETag): {current_etag}")
        print(f"    - Asset Name: {asset_to_delete.get('name')}")

        # --- STEP 2: Confirm before deleting ---
        # This is a safety measure to prevent accidental deletions.
        # Comment this block out if you want the script to run without user interaction.
        confirm = input("\n[?] Are you sure you want to permanently delete this asset? (yes/no): ")
        if confirm.lower() != 'yes':
            print("\n--- Deletion Canceled by User ---")
            return

        # --- STEP 3: Send the DELETE request ---
        print(f"\n[2] Sending DELETE request for asset {ASSET_ID_TO_DELETE}...")
        client.delete_asset(ASSET_ID_TO_DELETE, current_etag)
        
        print("\n--- Asset Deleted Successfully! ---")
        print("The asset has been permanently removed from the server.")

    except HTTPError as e:
        if e.response.status_code == 404:
            print("\n--- Deletion Skipped: Asset Not Found ---")
            print(f"An asset with the ID '{ASSET_ID_TO_DELETE}' does not exist on the server.")
        
        elif e.response.status_code == 412:
            print("\n--- DELETION FAILED: Precondition Failed (Error 412) ---")
            print("This means the asset was modified by someone else after it was fetched.")
            print("Please re-run the script to try again with the latest version.")
        
        else:
            print(f"\n--- An HTTP error occurred ---")
            print(f"Status Code: {e.response.status_code}")
            print(f"Reason: {e.response.text}")
            
    except ValueError as e:
        print(f"\n--- A data error occurred ---")
        print(f"Error: {e}")

    except Exception as e:
        print(f"\n--- An unexpected error occurred ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
