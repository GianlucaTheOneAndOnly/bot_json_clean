import json
import gspread
import copy

# --- Configuration ---
SERVICE_ACCOUNT_FILE = 'config/google_credentials.json'
# ---------------------

def get_sheet_data_as_dicts(spreadsheet, sheet_name):
    """Opens a sheet and returns its data as a list of dictionaries."""
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()
    except gspread.WorksheetNotFound:
        print(f"Warning: Sheet '{sheet_name}' not found.")
        return []

def get_task_name(speed, channel_num, orientation, is_dna, is_temp_only):
    """
    Retourne l'ID de présélection ('presid') correct en fonction des règles
    déduites des exemples fournis.
    """
    PRESELECTION_IDS = {
        "temp": "111111111111111111111111",  # Updated to match working payload
        "vib": {
            "r_0_320": "653fb075c716f23c7ecb26ee",
            "r_320_640": "653fb04bc716f23c7ecb26ec",
            "r_640_1280": "653faff4c716f23c7ecb26ea",
            "r_1280_3600": "653fafc3c716f23c7ecb26e8",
            "r_3600_plus": "653faf8dc716f23c7ecb26e6",
        },
        "dna": {
            "r_0_160": "653faee1c716f23c7ecb26e2",
            "r_160_320": "653faecac716f23c7ecb26e0",
            "r_320_640": "653fae9ec716f23c7ecb26de",
            "r_640_1280": "653fae33c716f23c7ecb26dc",
            "r_1280_plus": "653fadddc716f23c7ecb26d9",
        }
    }

    if is_temp_only:
        return PRESELECTION_IDS["temp"]

    # S'assurer que la vitesse est un nombre pour la comparaison
    try:
        current_speed = float(speed)
    except (ValueError, TypeError):
        current_speed = 0 # Vitesse par défaut si non spécifiée

    if is_dna:
        if current_speed < 160:
            return PRESELECTION_IDS["dna"]["r_0_160"]
        elif 160 <= current_speed < 320:
            return PRESELECTION_IDS["dna"]["r_160_320"]
        elif 320 <= current_speed < 640:
            return PRESELECTION_IDS["dna"]["r_320_640"]
        elif 640 <= current_speed < 1280:
            return PRESELECTION_IDS["dna"]["r_640_1280"]
        else: # >= 1280
            return PRESELECTION_IDS["dna"]["r_1280_plus"]
    else: # Vibration standard
        if current_speed < 320:
            return PRESELECTION_IDS["vib"]["r_0_320"]
        elif 320 <= current_speed < 640:
            return PRESELECTION_IDS["vib"]["r_320_640"]
        elif 640 <= current_speed < 1280:
            return PRESELECTION_IDS["vib"]["r_640_1280"]
        elif 1280 <= current_speed <= 3600:
            return PRESELECTION_IDS["vib"]["r_1280_3600"]
        else: # > 3600
            return PRESELECTION_IDS["vib"]["r_3600_plus"]
            
    return None # Au cas où aucune condition ne serait remplie


def generate_flat_json(factory_filter: str, zone_filter: str, database_id: str):
    """
    Génère une structure JSON plate à partir d'une base de données Google Sheet.
    """
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        ss = gc.open_by_key(database_id)
    except Exception as e:
        raise Exception(f"Failed to connect to Google Sheets. Check credentials and sheet ID. Error: {e}")

    # 1. Lire les données de toutes les feuilles nécessaires
    asset_data = get_sheet_data_as_dicts(ss, 'Asset')
    component_data = get_sheet_data_as_dicts(ss, 'Component')
    installation_data = get_sheet_data_as_dicts(ss, 'Installation')
    gateway_data = get_sheet_data_as_dicts(ss, 'Gateway')
    
    upload_id_counter = 1
    all_elements = []
    asset_upload_ids = {}
    assets_map = {}

    # 2. Traiter les "Assets"
    factory = None
    valid_zones = set()
    for row in asset_data:
        if row.get('Factory') == factory_filter:
            factory = factory_filter
            if row.get('Zone'):
                valid_zones.add(row['Zone'])

    if not factory:
        raise ValueError(f"No factory found for filter: {factory_filter}")

    zones_to_process = set()
    if zone_filter:
        requested_zones = [z.strip() for z in zone_filter.split(',')]
        zones_to_process = {zone for zone in requested_zones if zone in valid_zones}
    else:
        zones_to_process = valid_zones
        
    print(f"Zones to process: {zones_to_process}")

    # Factory element - exact format from working payload
    factory_element = {
        "upload_id": upload_id_counter,
        "t": 16777216,
        "name": factory,
        "upload_path": []
    }
    upload_id_counter += 1
    all_elements.append(factory_element)
    
    zone_elements_map = {}

    # Zone elements - exact format from working payload
    for zone in zones_to_process:
        zone_element = {
            "upload_id": upload_id_counter,
            "t": 16777216,
            "name": zone,
            "upload_path": [factory_element["upload_id"]]
        }
        upload_id_counter += 1
        all_elements.append(zone_element)
        zone_elements_map[zone] = zone_element
    
    # Asset elements - exact format from working payload
    for row in asset_data:
        if row.get('Factory') == factory_filter and row.get('Zone') in zones_to_process:
            asset_id = row.get('Asset ID')
            if not asset_id: continue
            
            asset_upload_id = upload_id_counter
            upload_id_counter += 1
            
            zone_element = zone_elements_map[row['Zone']]
            
            # Build asset element with exact field order from working payload
            asset_element = {
                "upload_id": asset_upload_id,
                "t": 33554432,
                "name": row.get('Name') or 'Unnamed Asset',
                "upload_path": [factory_element["upload_id"], zone_element["upload_id"]]
            }

            # Add optional fields in the order they appear in working payload
            if (periodicity := row.get('Measurement periodicity')):
                if '24h' in periodicity: 
                    asset_element['batch_process'] = True
                elif '6h' in periodicity: 
                    asset_element['batch_process'] = False
            
            if (criticality := row.get('Criticality')):
                criticality_mapping = {'Low': 1, 'Medium': 3, 'High': 5}
                if criticality in criticality_mapping:
                    asset_element['criticalness'] = criticality_mapping[criticality]

            if (picture := row.get('Location picture File Name')): 
                asset_element['picture'] = picture

            if str(row.get('Variable speed')).upper() == 'TRUE': 
                asset_element['variable_speed'] = True
            elif str(row.get('Variable speed')).upper() == 'FALSE': 
                asset_element['variable_speed'] = False

            # Datasheet field - always include, exactly as in working payload
            datasheet_cols = ['TAG', 'Area/Room', 'Level', 'Asset Comment', 'Measurement periodicity']
            datasheet_parts = [f"{col}: {row.get(col, '')}" for col in datasheet_cols]
            asset_element['datasheet'] = ", ".join(datasheet_parts)
            
            all_elements.append(asset_element)
            asset_upload_ids[asset_id] = asset_upload_id
            assets_map[asset_id] = asset_element

    # 3. Traiter les "Components" - Only if there are components with installations
    component_upload_ids = {}
    components_map = {}
    
    coupling_type_values = {
        'Direct': 0, 'Belt': 2, 'Gear': 1, 'Hydraulic coupling': 4, 'Poulie courroie': 2, 'Chain': 5, 
        'Flexible': 5, 'Poullie Courroies': 2, 'Fluid': 4, 'Cardan': 5, 'Accouplement caoutchouc': 5, 
        'Pneumabloc Jaune': 5, 'Courroies': 2, 'Étoile (tampons)': 5, 'Direct (Monobloc Motoréducteur)': 0,
        'Fixed Coupler': 0, 'Fixed': 0, 'Catena': 5, 'Direct coupling': 0, 'Belts': 2, 'direct': 0, 
        'Magnetkupplung': 3, 'Poulie/courroies': 2, 'Courroie': 2, 'Accouplement': 5, 'Shim': 5, 
        'Belt coupling': 2, 'DIRECT COUPLING': 0, 'Elastomeric Coupling': 5
    }

    for row in component_data:
        asset_id = row.get('Asset ID')
        if not asset_upload_ids.get(asset_id): continue
        component_id = row.get('Component ID')
        if not component_id: continue

        parent_asset_element = assets_map[asset_id]
        component_element = {
            "upload_id": upload_id_counter,
            "t": 33554437,
            "name": row.get('Name') or 'Unnamed Component',
            "upload_path": parent_asset_element["upload_path"] + [parent_asset_element["upload_id"]],
            "assetId": asset_id
        }
        
        if (num_shafts := row.get('Number of shafts')): component_element['number_of_shafts'] = int(num_shafts)
        if (brand := row.get('Brand')): component_element['brand'] = brand
        if (model := row.get('Model')): component_element['model'] = model
        if (speed := row.get('Nominal Speed (RPM)')): component_element['speed'] = float(speed)
        if (power := row.get('Power')): component_element['power'] = float(power)
        if (power_unit := row.get('Power Unit')): component_element['power_unit'] = 110 if power_unit == 'HP' else 28
        if (coupling_str := row.get('Coupling type')):
            if coupling_str in coupling_type_values: component_element['coupling_type'] = coupling_type_values[coupling_str]
        if str(row.get('Greaseable')).upper() == 'TRUE': component_element['lubrication'] = 1
        elif str(row.get('Greaseable')).upper() == 'FALSE': component_element['lubrication'] = 0
        if (lubricant := row.get('Lubricant')): component_element['lubricant'] = lubricant
        if (pic := row.get('Picture File name')): component_element['picture'] = pic
        if (comp_type := row.get('Component Type')): component_element['component_type'] = comp_type

        all_elements.append(component_element)
        component_upload_ids[component_id] = component_element['upload_id']
        components_map[component_id] = component_element
        upload_id_counter += 1


    # 4. Prétraiter les "Installations"
    installations_map = {}
    component_de_or_nde_map = {}
    for row in installation_data:
        component_id = row.get('Component ID')
        if component_id not in component_upload_ids: continue
        de_or_nde_str = row.get('DE or NDE', '')
        de_or_nde = 'NDE' if 'outboard' in de_or_nde_str.lower() else ('DE' if 'inboard' in de_or_nde_str.lower() else de_or_nde_str)
        if not de_or_nde: continue
        installations_map.setdefault(component_id, {}).setdefault(de_or_nde, []).append(row)
        component_de_or_nde_map.setdefault(component_id, set()).add(de_or_nde)

    # --- MODIFIED SECTION START ---
    # 5. Finaliser les composants et créer les installations, points de mesure, etc.
    # This entire section has been rewritten for correctness and clarity.

    # Identify the original "template" components that have installations. They will be replaced.
    component_ids_with_installations = set(component_de_or_nde_map.keys())
    upload_ids_to_remove = {
        component_upload_ids[cid] 
        for cid in component_ids_with_installations 
        if cid in component_upload_ids
    }

    # Filter out the "template" components that we are about to replace.
    all_elements = [
        e for e in all_elements 
        if not (e.get('t') == 33554437 and e.get('upload_id') in upload_ids_to_remove)
    ]

    # Now, iterate through components with installations and create the final, specific versions (e.g., DE/NDE).
    for component_id, de_or_nde_list in component_de_or_nde_map.items():
        original_component = components_map[component_id]
        base_name = original_component['name']

        for de_or_nde in de_or_nde_list:
            # Always work with a fresh copy to avoid side-effects.
            new_component = copy.deepcopy(original_component)
            
            # If a component is split (e.g., into DE and NDE), each new part needs a unique ID.
            # If it's not split (only one side exists), it correctly reuses the original ID from the deepcopy.
            if len(de_or_nde_list) > 1:
                new_component['upload_id'] = upload_id_counter
                upload_id_counter += 1
            
            new_component['name'] = f"{base_name} - {de_or_nde}"
            if 'outboard' in de_or_nde.lower() or 'nde' in de_or_nde.lower(): new_component['de_or_nde'] = 0
            elif 'inboard' in de_or_nde.lower() or 'de' in de_or_nde.lower(): new_component['de_or_nde'] = 1

            installations_for_this = installations_map.get(component_id, {}).get(de_or_nde, [])
            
            if installations_for_this:
                first_install_row = installations_for_this[0]
                if (ds_orient_str := first_install_row.get('Driveshaft orientation')) == 'Vertical': new_component['driveshaft_orientation'] = 0
                elif ds_orient_str == 'Horizontal': new_component['driveshaft_orientation'] = 1
                if (ts_orient_str := first_install_row.get('Transmitter Orientation')) == 'Vertical': new_component['transmitter_orientation'] = 0
                elif ts_orient_str == 'Horizontal': new_component['transmitter_orientation'] = 1
                elif ts_orient_str == 'Axial': new_component['transmitter_orientation'] = 2

            all_elements.append(new_component)
            
            for install_row in installations_for_this:
                asset_id = new_component['assetId']
                asset_element = assets_map[asset_id]
                serial_number = install_row.get('Serial Number', '')
                
                # Installation element - exact format from accepted payload
                installation_element = {
                    "t": 33554435,
                    "name": f"{serial_number} - {asset_element['name']}",
                    "serialnumber": serial_number,
                    "mac": install_row.get('Mac address'),
                    "upload_id": upload_id_counter,
                    "upload_path": new_component["upload_path"] + [new_component["upload_id"]]
                }
                upload_id_counter += 1
                
                if (speed := install_row.get('Nominal Speed (RPM)')): 
                    installation_element['nominal_speed'] = float(speed)
                
                # Add installation-specific fields from the accepted payload
                if (ts_orient_str := install_row.get('Transmitter Orientation')) == 'Vertical': 
                    installation_element['transmitter_orientation'] = 0
                elif ts_orient_str == 'Horizontal': 
                    installation_element['transmitter_orientation'] = 1
                elif ts_orient_str == 'Axial': 
                    installation_element['transmitter_orientation'] = 2
                
                installation_element['transmitter_mounting_method'] = 2  # Default value from example
                
                all_elements.append(installation_element)
                
                matching_types = ["WM704001131", "WM712121121", "WM500331141", "G23", "WM50033114100", "WM51033114102", "WM50033114106", "WM51033114106", "WM50033114102", "WM51033144100", "WM50033114108", "WM51033134101", "WM51033144101"]
                if install_row.get('Type') in matching_types:
                    ds_orient, ts_orient = install_row.get('Driveshaft orientation'), install_row.get('Transmitter Orientation')
                    orientation_mapping = {
                        "Horizontal_Vertical": {"V": 3, "H": 2, "A": 1, "dna_orient": "V"}, 
                        "Horizontal_Horizontal": {"V": 2, "H": 3, "A": 1, "dna_orient": "H"},
                        "Horizontal_Axial": {"V": 1, "H": 2, "A": 3, "dna_orient": "A"}, 
                        "Vertical_Vertical": {"V": 3, "H": 2, "A": 1, "dna_orient": "V"},
                        "Vertical_Horizontal": {"V": 2, "H": 3, "A": 1, "dna_orient": "H"}, 
                        "Vertical_Axial": {"V": 1, "H": 2, "A": 3, "dna_orient": "A"}
                    }
                    mapping = orientation_mapping.get(f"{ds_orient}_{ts_orient}")
                    if not mapping: continue
                    
                    # Create channel elements first - exact format from accepted payload
                    channels_info = [
                        (3, "Channel 3", 7),
                        (2, "Channel 2", 7), 
                        (1, "Channel 1", 7),
                        (4, "Temp. sensor", 7)
                    ]
                    
                    for channel_num, channel_name, sensor_type in channels_info:
                        channel_element = {
                            "upload_id": upload_id_counter,
                            "t": 33554436,
                            "name": channel_name,
                            "upload_path": installation_element["upload_path"] + [installation_element["upload_id"]],
                            "channel": channel_num,
                            "sensortype": sensor_type
                        }
                        upload_id_counter += 1
                        all_elements.append(channel_element)
                    
                    base_comp_name = f"{new_component.get('component_type', 'Comp')} - {de_or_nde}"
                    sn_suffix = str(serial_number)[-6:] if serial_number else ""
                    speed = installation_element.get('nominal_speed') or new_component.get('speed')
                    
                    # Create measurement points - exact format from accepted payload
                    for orientation, channel_num in mapping.items():
                        if orientation == "dna_orient": continue
                        mp_element = {
                            "upload_id": upload_id_counter,
                            "t": 16777218,
                            "name": f"{sn_suffix} - {base_comp_name} {orientation}",
                            "upload_path": new_component["upload_path"] + [new_component["upload_id"]],
                            "transmitter_upload_id": installation_element["upload_id"],
                            "speed": speed,
                            "preselection": get_task_name(speed, channel_num, orientation, False, False)
                        }
                        upload_id_counter += 1
                        all_elements.append(mp_element)
                    
                    idna_element = {
                        "upload_id": upload_id_counter,
                        "t": 16777218,
                        "name": f"{sn_suffix} - {base_comp_name} {mapping['dna_orient']} - I-DNA",
                        "upload_path": new_component["upload_path"] + [new_component["upload_id"]],
                        "speed": speed,
                        "preselection": get_task_name(speed, 3, mapping['dna_orient'], True, False),
                        "dna": True
                    }
                    upload_id_counter += 1
                    all_elements.append(idna_element)
                    
                    temp_element = {
                        "upload_id": upload_id_counter,
                        "t": 16777218,
                        "name": f"{sn_suffix} - {base_comp_name} - Temp. sensor",
                        "upload_path": new_component["upload_path"] + [new_component["upload_id"]],
                        "speed": speed,
                        "preselection": get_task_name(speed, 4, "V", False, True),
                        "temp_only": True
                    }
                    upload_id_counter += 1
                    all_elements.append(temp_element)
    # --- MODIFIED SECTION END ---

    # 6. Traiter le matériel et les "Gateways"
    hardware_element = {
        "upload_id": upload_id_counter,
        "t": 16777216,
        "name": 'Hardware',
        "upload_path": [factory_element["upload_id"]]
    }
    upload_id_counter += 1
    all_elements.append(hardware_element)

    hardware_gateway_element = {
        "upload_id": upload_id_counter,
        "t": 16777216,
        "name": 'Gateway',
        "upload_path": [factory_element["upload_id"], hardware_element["upload_id"]]
    }
    upload_id_counter += 1
    all_elements.append(hardware_gateway_element)
    
    hardware_gateway_zone_upload_ids = {}
    for row in gateway_data:
        if row.get('Factory') == factory_filter and row.get('Zone') in zones_to_process:
            zone = row['Zone']
            if zone not in hardware_gateway_zone_upload_ids:
                zone_upload_id = upload_id_counter
                upload_id_counter += 1
                gateway_zone_element = {
                    "upload_id": zone_upload_id,
                    "t": 16777216,
                    "name": zone,
                    "upload_path": [factory_element["upload_id"], hardware_element["upload_id"], hardware_gateway_element["upload_id"]]
                }
                all_elements.append(gateway_zone_element)
                hardware_gateway_zone_upload_ids[zone] = zone_upload_id

            serial_number = row.get('Serial number', '')
            gateway_element = {
                "upload_id": upload_id_counter,
                "t": 33554433,
                "name": serial_number or 'Unnamed Gateway',
                "upload_path": [factory_element["upload_id"], hardware_element["upload_id"], hardware_gateway_element["upload_id"], hardware_gateway_zone_upload_ids[zone]],
                "unique_id": serial_number
            }
            upload_id_counter += 1
            all_elements.append(gateway_element)

    # --- MODIFICATION ---
    # The final loop to delete 'assetId' has been removed, as the working payload requires this field.
    
    return json.dumps(all_elements, indent=2)

# --- Bloc d'exécution principal ---
if __name__ == '__main__':
    FACTORY = "Covestro Antwerpen"
    ZONE = "Polyether"
    DATABASE_ID = "13iNE-281Ga6eolH8PwnE7uTc6hZnS5NGs0o3jM6BGvg"

    print("Starting JSON generation...")
    try:
        json_output = generate_flat_json(FACTORY, ZONE, DATABASE_ID)
        
        with open('output.json', 'w') as f:
            f.write(json_output)
            
        print("\n✅ Le fichier `output.json` a été généré avec succès et est prêt à être utilisé.")

    except Exception as e:
        print(f"\n❌ Une erreur est survenue : {e}")