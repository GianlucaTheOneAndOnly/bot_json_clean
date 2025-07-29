temperature = {
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
    3, # channel (extremely important!!!)
    2,
    4
  ],
  "presid": "6576e3adb3c379dcb3bf985b",
  "presname": "Next Gen EXTERNAL TEMPERATURE ONLY",
  "rule": {
    "dtstart": 1752123078000, # timestamp Unix en millisecondes
    "freq": 3, # 1.Minutely, 2.Hourly, 3.Daily, 4.Weekly, 5.Monthly
    "interval": 12 # Occurence measurement
  },
  "tach": False #must be read as 'false' in the API
}

vib_300hz_1600 = {
  "presname": "Next Gen vib (< 320RPM) 300Hz / 1600 lines",
  "presid": "653fb075c716f23c7ecb26ee",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752123078000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire",
    3200,
    634,
    1,
    3000,
    30,
    15,
    0,
    1,
    2,
    1
  ],
  "statistics": {
    "vibration": [
      {
        "global_type": "acceleration",
        "fmin": 2,
        "fmax": 300
      },
      {
        "global_type": "velocity",
        "fmin": 2,
        "fmax": 300
      },
      {
        "global_type": "peak-peak"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

vib_600hz_1600 = {
  "presname": "Next Gen vib (320-640RPM) 600Hz / 1600 lines",
  "presid": "653fb04bc716f23c7ecb26ec",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752123719000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire",
    3200,
    1333,
    1,
    3000,
    30,
    15,
    0,
    2,
    2,
    1
  ],
  "statistics": {
    "vibration": [
      {
        "global_type": "acceleration",
        "fmin": 2,
        "fmax": 600
      },
      {
        "global_type": "velocity",
        "fmin": 2,
        "fmax": 600
      },
      {
        "global_type": "peak-peak"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

vib_1200hz_3200 = {
  "presname": "Next Gen vib (640-1280RPM) 1200Hz / 3200 lines",
  "presid": "653faff4c716f23c7ecb26ea",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752124103000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire",
    6400,
    2000,
    2,
    40,
    30,
    15,
    0,
    1,
    2,
    1
  ],
  "statistics": {
    "vibration": [
      {
        "global_type": "acceleration",
        "fmin": 2,
        "fmax": 1200
      },
      {
        "global_type": "velocity",
        "fmin": 2,
        "fmax": 1200
      },
      {
        "global_type": "peak-peak"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

vib_3000hz_6400 = {
  "presname": "Next Gen vib Default (1280-3600RPM) 3000Hz / 6400 lines",
  "presid": "653fafc3c716f23c7ecb26e8",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752124289000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire",
    12800,
    6666,
    1,
    3000,
    30,
    15,
    0,
    1,
    2,
    1
  ],
  "statistics": {
    "vibration": [
      {
        "global_type": "acceleration",
        "fmin": 10,
        "fmax": 3000
      },
      {
        "global_type": "velocity",
        "fmin": 10,
        "fmax": 3000
      },
      {
        "global_type": "peak-peak"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

vib_5000hz_6400 = {
  "presname": "Next Gen vib (>3600RPM) 5000Hz / 6400 lines",
  "presid": "653faf8dc716f23c7ecb26e6",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752126471000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire",
    12800,
    11111,
    1,
    3000,
    30,
    15,
    0,
    1,
    2,
    1
  ],
  "statistics": {
    "vibration": [
      {
        "global_type": "acceleration",
        "fmin": 10,
        "fmax": 5000
      },
      {
        "global_type": "velocity",
        "fmin": 10,
        "fmax": 5000
      },
      {
        "global_type": "peak-peak"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

vib_10000hz_6400 = {

  "presname": "Next Gen vib High Frq Meas 10000Hz / 6400 lines",
  "presid": "653fb0f7c716f23c7ecb26f1", # A cherche dans la liste de preselection
  "asset": "686d0908e2c3c75387dae7eb", # i-see id du mp
  "rule": {
    "dtstart": 1751982240000, # 
    "freq": "3", # DAILY
    "interval": 1 # integer
  },
  "params": [
    "acquire",
    12800,
    22222,
    1, 
    40,
    30,
    15,
    0,
    3, #channel
    2,
    1
  ],
  "statistics": {
    "vibration": [
      {
        "global_type": "acceleration",
        "fmin": 10,
        "fmax": 10000
      },
      {
        "global_type": "velocity",
        "fmin": 10,
        "fmax": 10000
      },
      {
        "global_type": "peak-peak"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

dna_125hz_1600 ={
  "presname": "Next Gen I-dna (80-160RPM) 125Hz / 1600 lines",
  "presid": "653faee1c716f23c7ecb26e2",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752124476000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire_dna",
    3200,
    160000,
    64,
    3000,
    0,
    0,
    0,
    1,
    0,
    32
  ],
  "statistics": {
    "dna": [
      {
        "global_type": "dna500",
        "noise_factor": 0.03
      },
      {
        "global_type": "dna12",
        "noise_factor": 0.03
      },
      {
        "global_type": "ave12",
        "noise_factor": 0.03
      },
      {
        "global_type": "stickslip"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

dna_250hz_1600 = {
  "presname": "Next Gen I-dna (160-320RPM) 250Hz / 1600 lines",
  "presid": "653faecac716f23c7ecb26e0",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752126140000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire_dna",
    3200,
    160000,
    32,
    3000,
    0,
    0,
    0,
    1,
    0,
    32
  ],
  "statistics": {
    "dna": [
      {
        "global_type": "dna500",
        "noise_factor": 0.03
      },
      {
        "global_type": "dna12",
        "noise_factor": 0.03
      },
      {
        "global_type": "ave12",
        "noise_factor": 0.03
      },
      {
        "global_type": "stickslip"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

dna_500hz_1600 = {
  "presname": "Next Gen I-dna (320-640RPM) 500Hz /1600 lines",
  "presid": "653fae9ec716f23c7ecb26de",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752126131000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire_dna",
    3200,
    160000,
    16,
    3000,
    0,
    0,
    0,
    1,
    0,
    32
  ],
  "statistics": {
    "dna": [
      {
        "global_type": "dna500",
        "noise_factor": 0.03
      },
      {
        "global_type": "dna12",
        "noise_factor": 0.03
      },
      {
        "global_type": "ave12",
        "noise_factor": 0.03
      },
      {
        "global_type": "stickslip"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

dna_1000hz_3200 ={
  "presname": "Next Gen I-dna (640-1280RPM) 1000Hz / 3200 lines",
  "presid": "653fae33c716f23c7ecb26dc",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752126477000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire_dna",
    6400,
    160000,
    8,
    3000,
    0,
    0,
    0,
    1,
    0,
    32
  ],
  "statistics": {
    "dna": [
      {
        "global_type": "dna500",
        "noise_factor": 0.03
      },
      {
        "global_type": "dna12",
        "noise_factor": 0.03
      },
      {
        "global_type": "ave12",
        "noise_factor": 0.03
      },
      {
        "global_type": "stickslip"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

dna_2000hz_3200 = {
  "presname": "Next Gen I-DNA Default (>1280RPM) 2000Hz / 3200 lines",
  "presid": "653fadddc716f23c7ecb26d9",
  "asset": "686e508012321d2cc2406605",
  "rule": {
    "dtstart": 1752128199000,
    "freq": "3",
    "interval": 1
  },
  "params": [
    "acquire_dna",
    6400,
    160000,
    4,
    3000,
    0,
    0,
    0,
    1,
    0,
    32
  ],
  "statistics": {
    "dna": [
      {
        "global_type": "dna500",
        "noise_factor": 0.03
      },
      {
        "global_type": "dna12",
        "noise_factor": 0.03
      },
      {
        "global_type": "ave12",
        "noise_factor": 0.03
      },
      {
        "global_type": "stickslip"
      }
    ]
  },
  "conditions": [],
  "tach": False
}

