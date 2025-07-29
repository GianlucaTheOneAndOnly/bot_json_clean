import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.client import initializer, Server

CUSTOMER_DB = "csupport"
asset_id_to_update = "6867dc54e70c98b317d7814e"

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

        # 2. GET: Retrieve current asset data for debugging
        print(f"\nRetrieving current asset data...")
        asset_data = client.get_asset(asset_id_to_update)
        current_etag = asset_data['_etag']
        
        print(f"Current asset structure:")
        print(f"- Asset ID: {asset_data.get('_id')}")
        print(f"- ETag: {current_etag}")
        print(f"- Current optionals keys: {list(asset_data.get('optionals', {}).keys())}")
        print(f"- Full optionals content: {json.dumps(asset_data.get('optionals', {}), indent=2)}")

        # 3. PATCH: Try different payload approaches
        
        # APPROACH 1: Minimal payload - only add picture
        print(f"\n--- APPROACH 1: Minimal payload ---")
        minimal_payload = {
            "optionals": {
                "picture": image_filename
            }
        }
        print(f"Minimal payload: {json.dumps(minimal_payload, indent=2)}")
        
        try:
            print("Attempting PATCH with minimal payload...")
            client.patch_asset(asset_id_to_update, current_etag, minimal_payload)
            print("SUCCESS: Minimal payload worked!")
        except Exception as e1:
            print(f"Minimal payload failed: {e1}")
            
            # APPROACH 2: Preserve existing optionals, add picture
            print(f"\n--- APPROACH 2: Preserve existing + add picture ---")
            existing_optionals = asset_data.get('optionals', {}).copy()
            existing_optionals['picture'] = image_filename
            
            # Remove potentially problematic fields
            fields_to_remove = ['oldpath', 'group', '_id', '_etag', '_created', '_updated', '_deleted']
            for field in fields_to_remove:
                existing_optionals.pop(field, None)
            
            preserve_payload = {
                "optionals": existing_optionals
            }
            print(f"Preserve payload: {json.dumps(preserve_payload, indent=2)}")
            
            try:
                # Refresh etag in case it changed
                asset_data = client.get_asset(asset_id_to_update)
                current_etag = asset_data['_etag']
                
                print("Attempting PATCH with preserve payload...")
                client.patch_asset(asset_id_to_update, current_etag, preserve_payload)
                print("SUCCESS: Preserve payload worked!")
            except Exception as e2:
                print(f"Preserve payload failed: {e2}")
                
                # APPROACH 3: Just the picture field at root level
                print(f"\n--- APPROACH 3: Picture at root level ---")
                root_payload = {
                    "picture": image_filename
                }
                print(f"Root payload: {json.dumps(root_payload, indent=2)}")
                
                try:
                    # Refresh etag again
                    asset_data = client.get_asset(asset_id_to_update)
                    current_etag = asset_data['_etag']
                    
                    print("Attempting PATCH with root payload...")
                    client.patch_asset(asset_id_to_update, current_etag, root_payload)
                    print("SUCCESS: Root payload worked!")
                except Exception as e3:
                    print(f"Root payload failed: {e3}")
                    
                    # APPROACH 4: Check if we need to use a different method
                    print(f"\n--- APPROACH 4: Debug API response ---")
                    print("All approaches failed. Let's check the API response details...")
                    
                    # Try to get more details about the error
                    try:
                        # Refresh etag one more time
                        asset_data = client.get_asset(asset_id_to_update)
                        current_etag = asset_data['_etag']
                        
                        # Try the original payload again but catch the full response
                        response = client.patch_asset(asset_id_to_update, current_etag, minimal_payload)
                        print(f"Unexpected success: {response}")
                    except Exception as e4:
                        print(f"Final error details: {e4}")
                        
                        # Check if the error response has more details
                        if hasattr(e4, 'response') and hasattr(e4.response, 'text'):
                            print(f"Error response body: {e4.response.text}")
                        
                        print("\nDebugging suggestions:")
                        print("1. Check if the asset exists and you have write permissions")
                        print("2. Verify the API endpoint URL is correct")
                        print("3. Check if there are required fields missing")
                        print("4. Verify the image filename format is accepted")
                        print("5. Check if the ETag is being handled correctly")

    except Exception as e:
        print(f"An error occurred in the main flow: {e}")
    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)
else:
    print("Could not proceed with script because API client initialization failed.")