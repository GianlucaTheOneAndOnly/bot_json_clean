# File: push_bulk_assets.py (Version finale pour création à la racine)

import json
import secrets
from api.client import initializer, Server
import data.asset_library as asset_library 

CUSTOMER_DB = "csupport"

client = initializer(customer_db=CUSTOMER_DB, server_region=Server.EU)

if client:
    try:
        full_batch_payload = []
        machine_name = "Nouvelle-Machine-Racine-1"
        
        # Définition des IDs temporaires
        machine_id = 1
        transmitter_id = 2
        mp_id = 3
        channel_id = 4
        
        # --- Construction de l'arborescence complète ---
        
        # 1. Machine à la racine (path vide)
        full_batch_payload.append(asset_library.get_machine_payload(machine_id, [], machine_name))
        
        # 2. Transmetteur, enfant de la machine
        full_batch_payload.append(asset_library.get_transmitter_payload(transmitter_id, [machine_id], f"{machine_name} - TX", secrets.token_hex(6).upper(), f"SN-{secrets.token_hex(4).upper()}"))
        
        # 3. Point de mesure, enfant de la machine
        full_batch_payload.append(asset_library.get_mp_payload(mp_id, [machine_id], f"{machine_name} - MP", transmitter_id, "67a626fde170c155d54f634d")) # Assurez-vous que cet ID est valide
        
        # 4. Canal, enfant du transmetteur
        full_batch_payload.append(asset_library.get_channel_payload(channel_id, [machine_id, transmitter_id], f"{machine_name} - CH1", 1))

        print("Payload final généré pour une arborescence complète :")
        print(json.dumps(full_batch_payload, indent=2))
        
        print("\nEnvoi du batch pour créer la nouvelle arborescence...")
        response = client.create_asset_batch(full_batch_payload)

        print("\nCréation en masse réussie !")
        print(json.dumps(response, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")