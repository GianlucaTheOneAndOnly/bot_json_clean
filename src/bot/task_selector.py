import data.task_payload_library as task
from typing import Any, Optional
import math

def selection_task_final(type: str, speed: Optional[int]) -> Optional[Any]:
    """
    Selects a task payload based on the given type and speed.

    Handles a None speed by providing a default payload for 'vib' and 'dna'.

    Returns:
        The selected payload or None if no match is found.
    """
    # 1. Handle default task assignment when speed is not provided.
    if speed is None:
        if type == 'vib':
            return task.vib_3000hz_6400
        if type == 'dna':
            return task.dna_2000hz_3200 

    # 2. Handle the special 'temp' case, which ignores speed.
    if type == 'temp':
        return task.temperature

    # This check is now needed here in case speed was None and type wasn't handled above
    if speed is None:
        return None

    # 3. Define speed ranges and the corresponding keys
    speed_map = {
        "very_low": (1, 80),
        "low": (81, 160),
        "low_mid": (161, 320),
        "mid": (321, 640),
        "high_mid": (641, 1000),
        "high": (1001, math.inf)
    }

    # 4. Find the correct speed key
    speed_key = None
    for key, (min_speed, max_speed) in speed_map.items():
        if min_speed <= speed <= max_speed:
            speed_key = key
            break

    if not speed_key:
        return None

    # 5. Use a nested dictionary to map type and speed to the payload
    payload_matrix = {
        'vib': {
            "very_low": task.vib_300hz_1600,
            "low": task.vib_600hz_1600,
            "low_mid": task.vib_1200hz_3200,
            "mid": task.vib_3000hz_6400,
            "high_mid": task.vib_5000hz_6400,
            "high": task.vib_10000hz_6400
        },
        'dna': {
            "very_low": task.dna_125hz_1600,
            "low": task.dna_250hz_1600,
            "low_mid": task.dna_500hz_1600,
            "mid": task.dna_1000hz_3200,
            "high_mid": task.dna_2000hz_3200,
        }
    }

    # 6. Retrieve the payload using the type and the determined speed_key
    return payload_matrix.get(type, {}).get(speed_key)