# File: push_fonctionnal_location.py

import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.client import IcareApiClient, initializer,process_hierarchy_to_dataframe, Server




CUSTOMER_DB = "csupport"

# Call the initializer function to get the client object
client = initializer(
    customer_db=CUSTOMER_DB,
    server_region=Server.EU
)

if client:
    # 1. First, find the parent node where you want to add the new asset.
    #    You would typically get this from your hierarchy DataFrame.
    #    Let's assume we found a 'Factory' with a specific ID.
    try:
        hierarchy_data = client.get_full_hierarchy()
        df_hierarchy = process_hierarchy_to_dataframe(hierarchy_data)
        
        # Find a factory to serve as the parent
        parent_factory_df = df_hierarchy[df_hierarchy['name'] == 'Test Jason']
        if parent_factory_df.empty:
            print("No factory found to add an asset to.")
        else:
            parent_node_id = parent_factory_df.iloc[0]['_id']
            parent_node_path = parent_factory_df.iloc[0]['path_ids']
            print(f"Parent node ID: {parent_node_id}")

            # 2. Construct the payload for the new asset.
            # The 'path' should be the parent's path plus the parent's ID.
            new_asset_path = parent_node_path + [parent_node_id]
            
            # 'perm' and 'perm_inh' are complex. A safe bet is to copy them
            # from an existing asset at the same level. For this example, we use dummy values.
            # In a real scenario, GET an existing asset to see what these look like.

            # --- Create a dummy image file for the example ---
            dummy_image_path = "temp_image.png"
            with open(dummy_image_path, "wb") as f:
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            # ---------------------------------------------------
            # Upload the image file
            print(f"\nUploading image {dummy_image_path}...")
            upload_response = client.upload_image(dummy_image_path)
            image_filename = upload_response['filename']
            print(f"Image uploaded successfully. iSee filename: {image_filename}")

            new_asset_payload = {
                'name': "New Pump Station 001",
                't': 33554432,  # Asset type from ITEM_TYPE constant
                'path': new_asset_path,
                'optionals': {
                    'criticality': 3,
                    'equipment_type': 101, # e.g., Pump
                    'speed' : 1500,
                    'picture': image_filename

                },
                'perm': [], # Copy from an existing asset
                'perm_inh': [] # Copy from an existing asset
            }

            # 3. Call the create_asset method
            print("\nCreating new asset...")
            created_asset = client.create_asset(new_asset_payload)
            print("Successfully created asset:")
            print(json.dumps(created_asset, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")

else: 
    print("Could not proceed with script because API client initialization failed.")
