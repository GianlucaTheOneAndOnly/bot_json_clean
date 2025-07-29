import pytest
import os
import json
import logging
from typing import List, Dict

# --- Imports from your project ---
# Ensure the path is correct to import your api modules
from api.client import IcareApiClient, initializer, Server, process_hierarchy_to_dataframe
import data.asset_library as asset_library

# --- Test Configuration ---
CUSTOMER_DB = "csupport"
PARENT_ASSET_NAME = "Test Jason"  # The name of the parent asset to search for

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Pytest Fixture ---

@pytest.fixture(scope="module")
def client() -> IcareApiClient:
    """
    Initializes the API client once per test module.
    Fails the test run if initialization is unsuccessful.
    """
    log.info("Initializing iCare API client for testing...")
    client_instance = initializer(customer_db=CUSTOMER_DB, server_region=Server.EU)
    if not client_instance:
        pytest.fail("API client initialization failed.")
    log.info("Client initialized successfully.")
    return client_instance

# --- Core Logic (Refactored into a function) ---

def create_full_asset_structure(client: IcareApiClient, parent_node_id: str, parent_node_path: List[str]) -> List[str]:
    """
    Creates a nested structure of assets (asset, transmitter, mp, channel)
    under a given parent.

    Args:
        client: The IcareApiClient instance.
        parent_node_id: The _id of the parent asset.
        parent_node_path: The path_ids of the parent asset.

    Returns:
        A list of IDs of all created assets for cleanup.
    """
    created_ids = []
    dummy_image_path = "temp_image.png"

    try:
        # 1. Create and Upload a dummy image
        with open(dummy_image_path, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        upload_response = client.upload_image(dummy_image_path)
        image_filename = upload_response['filename']
        log.info(f"Image uploaded successfully. Filename: {image_filename}")

        # 2. Create the main asset
        path_for_main_asset = parent_node_path + [parent_node_id]
        payload = asset_library.new_asset_payload
        payload['path'] = path_for_main_asset
        payload['optionals']['picture'] = image_filename
        
        log.info("\nCreating new asset...")
        created_asset = client.create_asset(payload)
        asset_id = created_asset['_id']
        created_ids.append(asset_id)
        log.info(f"Successfully created asset with ID: {asset_id}")

        # 3. Create the transmitter
        path_for_children = path_for_main_asset + [asset_id]
        payload = asset_library.new_transmitter_payload
        payload['path'] = path_for_children
        
        log.info("\nCreating new transmitter...")
        created_transmitter = client.create_asset(payload)
        transmitter_id = created_transmitter['_id']
        created_ids.append(transmitter_id)
        log.info(f"Successfully created transmitter with ID: {transmitter_id}")

        # 4. Create the Measurement Point (MP)
        payload = asset_library.new_mp_payload
        payload['path'] = path_for_children
        payload['optionals']['transmitter'] = transmitter_id
        
        log.info("\nCreating new MP...")
        created_mp = client.create_asset(payload)
        mp_id = created_mp['_id']
        created_ids.append(mp_id)
        log.info(f"Successfully created MP with ID: {mp_id}")

        # 5. Create the Channel
        path_for_channel = path_for_children + [transmitter_id]
        payload = asset_library.new_channel_payload
        payload['path'] = path_for_channel
        
        log.info("\nCreating new channel...")
        created_channel = client.create_asset(payload)
        channel_id = created_channel['_id']
        created_ids.append(channel_id)
        log.info(f"Successfully created channel with ID: {channel_id}")

        return created_ids

    finally:
        # Clean up the dummy image file
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)

# --- Pytest Test Function ---

def test_create_and_delete_asset_structure(client: IcareApiClient):
    """
    Tests the end-to-end process of creating a full asset structure and ensures cleanup.
    """
    created_asset_ids = []
    try:
        # SETUP: Find the parent node to build under
        log.info(f"Searching for parent asset named '{PARENT_ASSET_NAME}'...")
        hierarchy_data = client.get_full_hierarchy()
        df_hierarchy = process_hierarchy_to_dataframe(hierarchy_data)
        parent_df = df_hierarchy[df_hierarchy['name'] == PARENT_ASSET_NAME]

        assert not parent_df.empty, f"Setup failed: Parent asset '{PARENT_ASSET_NAME}' not found."
        
        parent_node_id = parent_df.iloc[0]['_id']
        parent_node_path = parent_df.iloc[0]['path_ids']
        log.info(f"Found parent node ID: {parent_node_id}")

        # ACT: Call the core logic to create the assets
        created_asset_ids = create_full_asset_structure(client, parent_node_id, parent_node_path)

        # ASSERT: Verify that assets were created
        assert created_asset_ids, "Function did not return any created asset IDs."
        assert len(created_asset_ids) == 4, "Expected 4 assets to be created (asset, tx, mp, channel)."
        log.info(f"✅ Assertion successful: {len(created_asset_ids)} assets created.")

        # Optional: A more robust check could fetch one of the assets to verify it exists
        fetched_asset = client.get_asset(created_asset_ids[0])
        assert fetched_asset is not None
        assert fetched_asset['_id'] == created_asset_ids[0]
        log.info(f"✅ Verification successful: Fetched asset {created_asset_ids[0]} from API.")

    finally:
        # CLEANUP: Delete all created assets, even if assertions fail
        if not created_asset_ids:
            log.warning("No assets were created, skipping cleanup.")
            return
            
        log.info(f"\n--- Starting cleanup for {len(created_asset_ids)} assets ---")
        
        # Delete in reverse order of creation to handle dependencies
        for asset_id in reversed(created_asset_ids):
            try:
                log.info(f"Deleting asset {asset_id}...")
                # To delete, we need the asset's _etag (version)
                asset_to_delete = client.get_asset(asset_id)
                if asset_to_delete:
                    client.delete_asset(asset_id, asset_to_delete['_etag'])
                    log.info(f"Successfully deleted asset {asset_id}.")
                else:
                    log.warning(f"Could not find asset {asset_id} to delete (already gone?).")
            except Exception as e:
                log.error(f"Failed to delete asset {asset_id}: {e}")
        log.info("--- Cleanup complete ---")