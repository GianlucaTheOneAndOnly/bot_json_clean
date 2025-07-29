import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.client import initializer, Server

CUSTOMER_DB = "csupport"
asset_id_to_update = "6867ea08745ac0bb4337274c"

# Call the initializer function to get the client object
client = initializer(
    customer_db=CUSTOMER_DB,
    server_region=Server.EU
)

if client:
    try:
        # --- Create a dummy image file for the example ---
        dummy_image_path = "temp_image.png"
        with open(dummy_image_path, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        # ---------------------------------------------------

        # 1. POST: Upload the image file
        print(f"\nUploading image {dummy_image_path}...")
        upload_response = client.upload_image(dummy_image_path)
        image_filename = upload_response['filename']
        print(f"Image uploaded successfully. iSee filename: {image_filename}")

        # 2. GET: Retrieve current asset data BEFORE update
        print(f"Retrieving current asset data...")
        asset_data_before = client.get_asset(asset_id_to_update)
        current_etag = asset_data_before['_etag']
        
        print(f"BEFORE UPDATE:")
        print(f"- Asset ID: {asset_data_before.get('_id')}")
        print(f"- Name: {asset_data_before.get('name')}")
        print(f"- Type (t): {asset_data_before.get('t')}")
        print(f"- ETag: {current_etag}")
        print(f"- Existing picture: {asset_data_before.get('optionals', {}).get('picture', 'None')}")
        
        # 3. PATCH: Update asset with MINIMAL changes
        # Only update the picture field in optionals, keep everything else the same
        
        existing_optionals = asset_data_before.get('optionals', {}).copy()
        existing_optionals['picture'] = image_filename
        
        # Create minimal payload - only include required fields and the updated optionals
        patch_payload = {
            "name": asset_data_before.get('name'),  # Required field - keep existing
            "t": asset_data_before.get('t'),        # Required field - keep existing
            "optionals": existing_optionals         # Updated optionals with picture
        }
        
        print(f"\nLinking image to asset {asset_id_to_update}...")
        print(f"Payload being sent: {json.dumps(patch_payload, indent=2)}")
        
        # Make the PATCH request
        print("Executing PATCH request...")
        result = client.patch_asset(asset_id_to_update, current_etag, patch_payload)
        
        print(f"PATCH result: {result}")
        
        # 4. VERIFY: Check if the asset still exists and was updated correctly
        print(f"\nVerifying asset after PATCH...")
        
        try:
            asset_data_after = client.get_asset(asset_id_to_update)
            
            print(f"AFTER UPDATE:")
            print(f"- Asset ID: {asset_data_after.get('_id')}")
            print(f"- Name: {asset_data_after.get('name')}")
            print(f"- Type (t): {asset_data_after.get('t')}")
            print(f"- ETag: {asset_data_after.get('_etag')}")
            print(f"- Updated picture: {asset_data_after.get('optionals', {}).get('picture', 'None')}")
            
            # Check if the picture was actually updated
            if asset_data_after.get('optionals', {}).get('picture') == image_filename:
                print("\n✅ SUCCESS: Asset updated successfully!")
                print(f"   Picture field now contains: {image_filename}")
            else:
                print("\n❌ WARNING: Asset exists but picture was not updated properly")
                print(f"   Expected: {image_filename}")
                print(f"   Got: {asset_data_after.get('optionals', {}).get('picture')}")
                
            # Check if any other fields were accidentally modified
            fields_to_check = ['name', 't']
            for field in fields_to_check:
                if asset_data_before.get(field) != asset_data_after.get(field):
                    print(f"⚠️  WARNING: Field '{field}' was changed!")
                    print(f"   Before: {asset_data_before.get(field)}")
                    print(f"   After: {asset_data_after.get(field)}")
            
        except Exception as verify_error:
            print(f"❌ CRITICAL ERROR: Cannot retrieve asset after PATCH!")
            print(f"   This might mean the asset was deleted or corrupted!")
            print(f"   Error: {verify_error}")
            
            # Try to check if asset exists at all
            try:
                print("Checking if asset exists...")
                check_result = client.get_asset(asset_id_to_update)
                print(f"Asset still exists: {check_result.get('_id')}")
            except:
                print("❌ ASSET DOES NOT EXIST ANYMORE!")

    except Exception as e:
        print(f"An error occurred: {e}")
        
        # Enhanced error handling
        if hasattr(e, 'response'):
            print(f"Status code: {e.response.status_code}")
            if hasattr(e.response, 'text'):
                print(f"Response text: {e.response.text}")
                
    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)
else:
    print("Could not proceed with script because API client initialization failed.")