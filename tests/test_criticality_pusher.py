import pytest
import sys
import os
import logging
from typing import Optional, Dict, List

# Add the parent directory to the path to allow imports from the 'api' and 'data' folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Imports from your project ---
from api.client import IcareApiClient, initializer, Server
import data.asset_library as asset_library # Used for creating a test asset

# --- Test Configuration ---
CUSTOMER_DB = "csupport"
NEW_CRITICALITY_VALUE = 325 # The new value we will test setting
# Define a stable parent asset under which temporary assets will be created.
PARENT_ASSET_NAME = "Test Jason" 

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Pytest Fixture ---

@pytest.fixture(scope="module")
def client() -> IcareApiClient:
    """
    Initializes the API client once per test module.
    """
    log.info("Initializing iCare API client for testing...")
    client_instance = initializer(customer_db=CUSTOMER_DB, server_region=Server.EU)
    if not client_instance:
        pytest.fail("API client initialization failed.")
    log.info("Client initialized successfully.")
    return client_instance

# --- Test Function ---

def test_asset_criticality_update(client: IcareApiClient):
    """
    Tests the asset update functionality in a self-contained manner.
    1. Finds a parent asset to create children under.
    2. Creates a temporary asset.
    3. Updates its criticality.
    4. Verifies the update was successful.
    5. Deletes the temporary asset to ensure cleanup.
    """
    temp_asset_id = None
    try:
        # 1. SETUP - PART A: Find the parent node to build under
        log.info(f"\n--- SETUP: Searching for parent asset named '{PARENT_ASSET_NAME}' ---")
        hierarchy_data = client.get_full_hierarchy()
        parent_asset_data = _find_asset_by_name(hierarchy_data, PARENT_ASSET_NAME)
        
        assert parent_asset_data is not None, f"SETUP FAILED: Parent asset '{PARENT_ASSET_NAME}' not found."
        
        parent_node_id = parent_asset_data['_id']
        parent_node_path = parent_asset_data.get('path_ids', parent_asset_data.get('path', [])) # Handle both possible key names
        log.info(f"Found parent node ID: {parent_node_id}")

        # 1. SETUP - PART B: Create a temporary asset inside the parent
        log.info("--- SETUP: Creating a temporary asset for the test ---")
        payload = asset_library.new_asset_payload
        payload['name'] = "Temporary Criticality Test Asset"
        payload['path'] = parent_node_path + [parent_node_id]
        
        created_asset = client.create_asset(payload)
        assert created_asset and "_id" in created_asset, "SETUP FAILED: Could not create temporary asset."
        
        temp_asset_id = created_asset["_id"]
        log.info(f"SETUP complete. Created temporary asset with ID: {temp_asset_id}")

        # 2. ACT: Call the helper function to update the asset's criticality
        log.info(f"--- ACT: Attempting to update criticality for asset {temp_asset_id} ---")
        # We don't need to store the return value, as we only care if it raises an exception.
        _update_asset_criticality_helper(client, temp_asset_id, NEW_CRITICALITY_VALUE)

        # 3. ASSERT: Verify that the update was successful by re-fetching the asset
        log.info("--- ASSERT: Verifying the update by re-fetching the asset ---")
        
        # FIX: The most reliable check is to get the asset again and inspect its values.
        fetched_asset = client.get_asset(temp_asset_id)
        assert fetched_asset is not None, "Could not re-fetch the asset after update."
        
        final_criticality = fetched_asset.get("optionals", {}).get("criticality")
        
        assert final_criticality == NEW_CRITICALITY_VALUE, \
            f"ASSERT FAILED: Criticality was not updated. Expected {NEW_CRITICALITY_VALUE}, got {final_criticality}."
        
        log.info(f"ASSERT successful. Asset criticality is now {final_criticality}.")

    finally:
        # 4. TEARDOWN: Delete the temporary asset, even if the test fails
        if temp_asset_id:
            log.info(f"\n--- TEARDOWN: Deleting temporary asset {temp_asset_id} ---")
            try:
                asset_to_delete = client.get_asset(temp_asset_id)
                if asset_to_delete:
                    client.delete_asset(temp_asset_id, asset_to_delete['_etag'])
                    log.info(f"TEARDOWN successful. Deleted asset {temp_asset_id}.")
                else:
                    log.warning(f"TEARDOWN notice: Could not find asset {temp_asset_id} to delete (already gone?).")
            except Exception as e:
                log.error(f"TEARDOWN FAILED: Could not delete asset {temp_asset_id}. Error: {e}", exc_info=True)


# --- Helper Functions (prefixed with _ so pytest ignores them) ---

def _find_asset_by_name(hierarchy: List[Dict], name: str) -> Optional[Dict]:
    """
    Iterates through a list of asset dictionaries from the hierarchy 
    and returns the first one that matches the given name.
    """
    for asset in hierarchy:
        if asset.get("name") == name:
            return asset
    return None

def _update_asset_criticality_helper(client: IcareApiClient, asset_id: str, new_criticality: int) -> Optional[Dict]:
    """
    Helper function to update the 'criticality' of an asset. This is NOT a test.
    """
    asset_data = client.get_asset(asset_id)
    if not asset_data:
        log.error(f"Could not retrieve asset {asset_id} to update.")
        return None
    
    current_etag = asset_data['_etag']
    
    # Per user feedback, the payload must contain all original information.
    # We start with the full data object we just fetched.
    patch_payload = asset_data

    # Ensure the 'optionals' dictionary exists before modifying it.
    if 'optionals' not in patch_payload:
        patch_payload['optionals'] = {}
    
    # Set the new criticality value within the payload.
    patch_payload['optionals']['criticality'] = new_criticality

    # It's good practice to remove read-only fields like _id and _etag from the payload
    # before sending it back, as some APIs will reject the request otherwise.
    patch_payload.pop('_id', None)
    patch_payload.pop('_etag', None)
    
    log.info(f"Sending PATCH request for asset {asset_id} with full payload: {patch_payload}")
    # The return value is not used, but we let it return in case it's needed elsewhere.
    return client.update_asset(asset_id, current_etag, patch_payload)
