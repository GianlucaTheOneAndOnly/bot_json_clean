new_asset_payload = {
    'name': "Machine asset 1",
    't': 33554437,  # Asset type from ITEM_TYPE constant
    #'path': new_asset_path,
    'optionals': {
        'criticality': 3,
        'equipment_type': 101, # e.g., Pump
        'speed' : 1500,
        #'picture': image_filename
    },
    'perm': [], # Copy from an existing asset
    'perm_inh': [] # Copy from an existing asset
            }

new_transmitter_payload = {
    'name' : "Transmitter 1",
    't' : 33554435,
    'perm' : [],
    'perm_inh' : [],
    'optionals' : {
        "mac" : "Testing1",
        "serialnumber" : "DoYouSeeMe?",
        "appfirmware": "1700001b"
    }
}

new_mp_payload = {
    'name' : "MP 1",
    't' : 16777218,
    'perm':[],
    'perm_inh':[],
    'optionals' : {
        "speed" : 1500
    }

}

new_channel_payload = {
    'name' : "Channel 1",
    't' : 33554436,
    'perm' : [],
    'perm_inh' : [],
    'optionals' : {
        "ratio": 1500.0,
        "factor": 249.5,
        "sensortype": 7,
        "offset": 0.0,
        "temp": 10.0,
        "units": 9.98,
        "sensitivity": 25.0,
        "oldpath": [],
        "channel": 1
    }
}

new_gateway_payload = {
    'name' : "Gateway 1",
    't' : 33554433,
    'perm' : [],
    'perm_inh' : [],
}

default_task_payload = {
    "presname": "",
    "Presid": "",  # From GET /apiv4/preselections
    "Asset": "",  # ID of measurement point
    "Rule": {
        "dtstart": 1750927015663,
        "freq": "3",
        "interval": 1
    },
    "Params": ["acquire", 12800, 6666, 1, 3000, 30, 15, 0, 1, 2, 1],  # To be confirmed from GET /apiv4/preselections
    "Statistics": {
        "vibration": [
            {
                "global_type": "acceleration",
                "fmin": 10,
                "fmax": 3333
            },
            {
                "global_type": "velocity",
                "fmin": 10,
                "fmax": 3333
            },
            {
                "global_type": "peak-peak"
            }
        ]
    },
    "conditions": []
}

default_payload_tasks = {
  "_id": "",
  "_etag": "",
  "_links": {
    "self": {
      "href": "", #"/apiv4/tasks/686bcd6e9fc5be4b90a99e3f/task/686cc9481547e7de8874a906",
      "title": "task"
    },
    "parent": {
      "href": "/apiv4/tasks/686bcd6e9fc5be4b90a99e3f",
      "title": "task list"
    }
  },
  "_created": "Tue, 08 Jul 2025 07:31:20 GMT",
  "_updated": "Tue, 08 Jul 2025 07:31:20 GMT",
  "asset": "686bcd6e9fc5be4b90a99e3f",
  "statistics": {
    "temperature": [
      {
        "global_type": "temperature"
      }
    ]
  },
  "params": [
    "acquire",
    1,
    6666,
    1,
    3000,
    30,
    15,
    0,
    3, #this is the channel
    2,
    4
  ],
  "presid": "6576e3adb3c379dcb3bf985b",
  "presname": "Next Gen EXTERNAL TEMPERATURE ONLY",
  "rule": {
    "dtstart": "Tue, 08 Jul 2025 07:31:20 GMT",
    "freq": 4,
    "interval": 12
  },
  "tach": False #must be read as 'false' in the API
}

default_preselection = {
    "_id": "6576e3adb3c379dcb3bf985b",
    "_etag": "12762851340006395274",
    "_links": {
      "self": {
        "href": "/apiv4/preselections/6576e3adb3c379dcb3bf985b",
        "title": "preselection"
      }
    },
    "_updated": "Tue, 06 May 2025 09:34:35 GMT",
    "name": "Next Gen EXTERNAL TEMPERATURE ONLY",
    "parameters": [
      "acquire", # BEWARE NOT PRESENT IN SERVER DATA, VALUE ADDED IN POST_PROCESS
      1,
      6666,
      1,
      3000,
      30,
      15,
      0,
      4, # initial value : 2
      2,
      4
    ],
    "dna": False, #must be read as 'false' in the API
    "tach": False, #must be read as 'false' in the API
    "w30": True #must be read as 'True' in the API
  }


# Fichier : data/asset_library.py (Version Corrigée)

# Fichier : data/asset_library.py (Version Corrigée pour la machine)

def get_machine_payload(upload_id, path, name):
    # On reproduit EXACTEMENT la structure du payload qui fonctionne
    return {
        'upload_id': upload_id,
        'name': name,
        't': 33554437,
        'upload_path': path,
        'brand': "DefaultBrand",
        'speed': 1500,
        'power': 100,
        'power_unit': 28,
        'component_type': "DEFAULT_COMPONENT",
        # Ajout des derniers champs manquants pour être exhaustif
        'lubrication': 1,
        'assetId': f"ASSET_{name.replace(' ', '_')}",
        'driveshaft_orientation': 1,
        'transmitter_orientation': 0
    }



def get_transmitter_payload(upload_id, path, name, mac_address, serial_number):
    # mac et serialnumber sont à la racine
    return {
        'upload_id': upload_id,
        'name': name,
        't': 33554435, # Type Transmitter
        'upload_path': path,
        'mac': mac_address,
        'serialnumber': serial_number
    }

def get_mp_payload(upload_id, path, name, transmitter_upload_id, preselection_id):
    # transmitter_upload_id et preselection sont à la racine
    # Ceci résout également votre problème initial de préselection !
    return {
        'upload_id': upload_id,
        'name': name,
        't': 16777218, # Type MP
        'upload_path': path,
        'transmitter_upload_id': transmitter_upload_id,
        'speed': 1500,
        'preselection': preselection_id
    }

def get_channel_payload(upload_id, path, name, channel_number):
    # channel et sensortype sont à la racine
    return {
        'upload_id': upload_id,
        'name': name,
        't': 33554436, # Type Sensor/Channel
        'upload_path': path,
        'channel': channel_number,
        'sensortype': 7
    }