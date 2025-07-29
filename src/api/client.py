import concurrent.futures
import datetime
import json
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
import configparser
from typing import Optional

# --- Configuration and Constants ---

class Server(Enum):
    """Enumeration for available API servers."""
    EU = ""
    US = "-us"
    PREVIEW = "-preview"

ITEM_TYPE = {
    '16777216': "Functional location", '16777220': "Corp", '16777221': "Factory",
    '16777217': "Country", '16777222': "Zone", '33554432': "Asset", '16777218': "MP",
    '33554435': "Transmitter", '33554436': "Sensor", '33554434': "Range extender",
    '33554433': "Gateway"
}

TASKS_TEMPLATE_ID = [
    "5d36fd72d3e54323a29a86e4", "5d36fd72d3e54323a29a86e5", "5d36fd72d3e54323a29a86e6",
    "5d36fd72d3e54323a29a86e8", "5d36fd72d3e54323a29a86ea", "5d36fd72d3e54323a29a86ec",
    "5d36fd72d3e54323a29a86ed", "5d36fd72d3e54323a29a86ee", "5d36fd72d3e54323a29a86ef",
    "5d36fd72d3e54323a29a86f0", "5d36fd72d3e54323a29a86f1", "5d36fd72d3e54323a29a86f2",
    "61b31b05f88a745f8edd48b5", "61e82433d406c097acc29d21", "61e82433d406c097acc29d22",
    "61e82433d406c097acc29d23", "61e82433d406c097acc29d24", "61e82433d406c097acc29d25",
    "61e82433d406c097acc29d26", "62ea60e339d87b9f7aab402a", "639b413afd1545827b63d2be"
]


# --- Part 1: Refactored API Client ---

class IcareApiClient:
    """A client for interacting with the iSee/iCare Web API."""

    BASE_URL_TEMPLATE = "https://isee{server_suffix}.icareweb.com"

    def __init__(self, username: str, password: str, server: Server = Server.EU):

        self.username = username
        self.password = password
        self.server_suffix = server.value
        self.base_url = self.BASE_URL_TEMPLATE.format(server_suffix=self.server_suffix)
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Language": "en",
            "Accept": "application/json"
        })
        self.task_templates_cache = {}

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Centralized method for making API requests."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            if response.content:
                return response.json()
            return None
        except requests.exceptions.JSONDecodeError:
            # Handle cases where the response is not valid JSON
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request to {url}: {e}")
            raise

    def _fetch_all_paginated_data(self, endpoint: str, params: Optional[Dict] = None, page_size: int=1000 ) -> List[Dict]:
        """Fetches all items from a paginated API endpoint."""
        if params is None:
            params = {}
        
        params.update({"p": 1, "count": page_size})
        
        first_page = self._request("GET", endpoint, params=params)
        if not first_page or "_embedded" not in first_page:
            return []

        all_items = first_page["_embedded"]
        total_items = first_page["_meta"]["total"]
        
        # Use ThreadPoolExecutor for concurrent fetching of remaining pages
        pages_to_fetch = range(2, (total_items // page_size) + 2)
        
        def fetch_page(page_num):
            page_params = params.copy()
            page_params["p"] = page_num
            page_data = self._request("GET", endpoint, params=page_params)
            return page_data["_embedded"] if page_data and "_embedded" in page_data else []

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_page = {executor.submit(fetch_page, page): page for page in pages_to_fetch}
            for future in concurrent.futures.as_completed(future_to_page):
                all_items.extend(future.result())

        return all_items


    def login(self, customer_db: str) -> List[str]:
        """Authenticates the user and selects a customer database."""
        login_endpoint = "/apilogin/login"
        
        # Step 1: Initial Login to get token and available DBs
        credentials = {"username": self.username, "password": self.password}
        user_data = self._request("POST", login_endpoint, json=credentials)
        
        available_dbs = [db['db'] for db in user_data['dbs']]
        if customer_db not in available_dbs:
            raise ValueError(f"Database '{customer_db}' not available for this user.")

        self.session.headers["Authorization"] = f"Bearer {user_data['token']}"
        
        # Step 2: Select the database to get a specific token
        db_selection_endpoint = f"{login_endpoint}/{customer_db}"
        final_user_data = self._request("GET", db_selection_endpoint)
        self.session.headers["Authorization"] = f"Bearer {final_user_data['token']}"
        
        print(f"Successfully logged in to database '{customer_db}'.")
        return available_dbs

    def get_full_hierarchy(self, exclude_recycle_bin: bool = True) -> List[Dict]:
        """
        Gets the full asset hierarchy for the database.
        If exclude_recycle_bin is True, it filters out assets in the recycle bin.
        """
        if exclude_recycle_bin:
            # Get the root node ID to fetch only assets under it
            toplevels = self._request("GET", "/apiv4/assets/toplevels")
            if not toplevels:
                return []
            root_id = toplevels[0]["_id"]
            return self._fetch_all_paginated_data("/api/assets/v0/", params={"parent": root_id, "extra": "path"})
        else:
            return self._fetch_all_paginated_data("/api/assets/v0/", params={"extra": "path"})

    def get_asset(self, asset_id: str) -> Dict:
        """Retrieves details for a single asset."""
        return self._request("GET", f"/apiv4/assets/{asset_id}")

    def get_network_status(self) -> List[Dict]:
        """Retrieves the raw Net-Wi-Care network status."""
        return self._request("GET", "/apiv4/network/")

    def get_tasks(self, asset_id: str, task_id: str) -> List[Dict]:
        """Retrieves the raw Preselections."""
        return self._request("GET", f"/apiv4/tasks/{asset_id}/task/{task_id}")

    def get_preselections(self, tach: Optional[bool] = None) -> List[Dict]:
        """
        Fetches all available task preselections, handling pagination automatically.

        Args:
            tach (Optional[bool]): If specified, filters preselections
                                  based on the 'tach' flag.

        Returns:
            List[Dict]: A list of all preselection objects.
        """
        endpoint = "/apiv4/preselections/"
        params = {}
        
        # Add optional filters to the request parameters
        if tach is not None:
            params['tach'] = str(tach) # API expects 'true' or 'false' string

            # Add the required sorting parameters when filtering
            params['sort'] = '_id'
            params['direction'] = 1

        print(f"Fetching all preselections with params: {params}...")
        return self._fetch_all_paginated_data(endpoint, params, page_size=100)

    def get_trends(self, asset_id: str, start: datetime.datetime, end: datetime.datetime) -> List[Dict]:
        """Retrieves trend results for a given asset and time range."""
        params = {
            'creationfrom': int(start.timestamp() * 1000),
            'creationto': int(end.timestamp() * 1000)
        }
        return self._request("GET", f"/apiv4/assets/{asset_id}/trends", params=params)

    def get_latest_results(self, asset_id: str) -> List[Dict]:
        """Retrieves the latest results for an asset."""
        return self._request("GET", f"/apiv4/assets/{asset_id}/results/latests")

    def get_thresholds(self, measure_point_id: str) -> Dict:
        """Retrieves thresholds for a single measure point."""
        return self._request("GET", f"/apiv4/assets/{measure_point_id}/thresholds")

    def get_diagnoses(self, asset_id: str, start: datetime.datetime, end: datetime.datetime) -> List[Dict]:
        """Fetches all diagnoses for an asset within a date range."""
        endpoint = f"/apiv4/diagnoses/{asset_id}"
        params = {
            'creationfrom': int(start.timestamp() * 1000),
            'creationto': int(end.timestamp() * 1000)
        }
        return self._fetch_all_paginated_data(endpoint, params)
    
    def create_asset(self, asset_payload: Dict) -> Dict:
        """Creates a new asset."""
        return self._request("POST", "/apiv4/assets/", json=asset_payload)

    def create_asset_batch(self, batch_payload: List[Dict]) -> Dict:
        """
        Creates multiple assets in a single batch request.
        The payload should be a list of asset dictionaries.
        """
        # L'endpoint est le même que pour créer un seul asset,
        # mais le payload est une liste.
        return self._request("POST", "/apiv4/assets/", json=batch_payload)

    def delete_asset(self, asset_id: str, etag: str) -> None:
        # The endpoint is the specific resource URL for the asset.
        endpoint = f"/apiv4/assets/{asset_id}"

        # The 'If-Match' header is crucial for safe, conditional deletion.
        headers = self.session.headers.copy()
        headers['If-Match'] = etag
        
        # Use the session's 'delete' method with the specific headers.
        response = self.session.delete(
            f"{self.base_url}{endpoint}",
            headers=headers
        )
        
        # Raise an exception for any non-2xx status code.
        response.raise_for_status()
        
        # A successful DELETE returns no content, so we return None.
        return None

    
    # In IseeApiClient.py
    def create_task(self, task_payload: dict) -> dict:
        """Creates a new task."""
        return self._request("POST", "/apiv4/tasks/", json=task_payload)

    # --- NEW/UPDATED METHOD ---
    def update_asset(self, asset_id: str, etag: str, payload: Dict) -> Dict:
        """
        Safely updates (patches) an existing asset with a partial payload.
        The ETag is required for optimistic locking to prevent race conditions.

        Args:
            asset_id (str): The ID of the asset to update.
            etag (str): The _etag value from the last time the asset was fetched.
            payload (Dict): A dictionary containing only the fields to be changed.

        Returns:
            Dict: The full JSON of the updated asset from the server.
            
        Raises:
            requests.exceptions.HTTPError: If the server returns an error (e.g., 412
            Precondition Failed if the ETag is outdated, 404 Not Found, etc.).
        """
        # We call the session directly to easily add the custom 'If-Match' header
        # while preserving the other session headers like Authorization.
        headers = self.session.headers.copy()
        headers['If-Match'] = etag
        
        response = self.session.patch(
            f"{self.base_url}/apiv4/assets/{asset_id}",
            headers=headers,
            json=payload
        )
        
        # Raise an exception for non-2xx status codes
        response.raise_for_status()
        
        # Return the JSON body of the successful response
        return response.json() if response.content else None

    def upload_image(self, file_path: str) -> Dict:
        """Uploads an image file and returns its metadata (including the iSee filename)."""
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f)}
            # File uploads are special and don't always use the JSON helper
            response = self.session.post(f"{self.base_url}/apiv4/image/", files=files)
            response.raise_for_status()
            return response.json()
            
    def create_fault(self, fault_payload: Dict) -> Dict:
        """Creates a new fault associated with an asset."""
        return self._request("POST", "/apiv4/faults/", json=fault_payload)


# --- Part 2: Data Processing Functions ---

def process_hierarchy_to_dataframe(hierarchy_data: List[Dict]) -> pd.DataFrame:
    """Converts raw hierarchy data into a structured Pandas DataFrame."""
    if not hierarchy_data:
        return pd.DataFrame()

    id_to_name_map = {asset['_id']: asset['name'] for asset in hierarchy_data}
    processed_records = []
    for asset in hierarchy_data:
        record = {
            '_id': asset['_id'],
            'name': asset['name'],
            'type': ITEM_TYPE.get(str(asset.get('t'))),
            'path_ids': asset.get('path', [])
        }
        path_names = [id_to_name_map.get(node_id, 'Unknown') for node_id in record['path_ids']]
        for i, level_name in enumerate(path_names):
            record[f'level{i+1}'] = level_name
        processed_records.append(record)
    
    df = pd.DataFrame(processed_records)
    level_cols = sorted([col for col in df.columns if col.startswith('level')])
    other_cols = ['name', '_id', 'type', 'path_ids']
    df = df[level_cols + other_cols]
    return df

def process_network_status_to_dataframe(network_data: List[Dict], hierarchy_df: pd.DataFrame) -> pd.DataFrame:
    """Processes raw network status, flattens it, and merges it with hierarchy info."""
    if not network_data:
        return pd.DataFrame()
    
    flat_network_list = []
    def flatten_recursive(node: Dict, coordinator_mac: Optional[str] = None):
        for mac, details in node.items():
            record = {
                'mac': mac,
                'coordinator': coordinator_mac,
                'type': details.get('type'),
                'last_com': pd.to_datetime(details.get('last_com')),
                'batt': details.get('batt'),
                'child_count': len(details.get('children', {}))
            }
            flat_network_list.append(record)
            current_coordinator = mac if details.get('type') == 'C' else coordinator_mac
            if 'children' in details and details['children']:
                flatten_recursive(details['children'], current_coordinator)

    for gateway in network_data:
        flatten_recursive(gateway)
    return pd.DataFrame(flat_network_list)

def process_trends_to_dataframe(trends_data: List[Dict]) -> pd.DataFrame:
    """Converts raw trend data into a structured Pandas DataFrame."""
    if not trends_data:
        return pd.DataFrame()
    results_list = []
    for result in trends_data:
        for statistic in result.get('statistics', []):
            results_list.append({
                "meas_id": result['_id'],
                "asset_id": result['asset'],
                "status": statistic.get('status'),
                "type": statistic.get('global_type'),
                "value": statistic.get("value"),
                "time": pd.to_datetime(result.get('acqend'))
            })
    return pd.DataFrame(results_list)

def initializer(customer_db: str, 
                              server_region: Server = Server.EU, 
                              config_file: str = 'config/config.ini') -> Optional[IcareApiClient]:
    """
    Reads credentials from a config file, initializes, and returns an authenticated IcareApiClient.
    """
    config = configparser.ConfigParser()
    files_read = config.read(config_file)
    if not files_read:
        print(f"Error: The configuration file '{config_file}' was not found or is empty.")
        return None
    try:
        username = config.get('DEFAULT', 'USERNAME')
        password = config.get('DEFAULT', 'PASSWORD')
    except configparser.NoOptionError as e:
        print(f"Error: A required setting is missing from '{config_file}': {e}")
        return None

    try:
        print("Initializing and logging into iCare API client...")
        client = IcareApiClient(
            username=username,
            password=password,
            server=server_region
        )
        client.login(customer_db=customer_db)
        print("Client initialized and logged in successfully.")
        return client
    except Exception as e:
        print(f"Failed to initialize API client: {e}")
        return None


# --- Example Usage ---
if __name__ == '__main__':
    # This is a demonstration of how to use the class and functions.
    # Replace with your actual credentials and settings.
    # from getpass import getpass
    # USERNAME = input("Enter username: ")
    # PASSWORD = getpass("Enter password: ")
    
    # Dummy credentials for demonstration
    USERNAME = "iseeadmin@icareweb.com"
    PASSWORD = "carwu5-qobxup-cynteK"
    BQ_json_path = "sql-cloud-for-cargill-260414-d27681b597d8.json"
    CUSTOMER = "valtris"
    
    print("Initializing API Client...")
    try:
        # 1. Initialize the client
        client = IcareApiClient(username=USERNAME, password=PASSWORD, server=Server.EU)
        
        # 2. Login to the specific customer database
        client.login(customer_db=CUSTOMER)
        
        # 3. Fetch data using the client
        print("\nFetching full asset hierarchy...")
        raw_hierarchy = client.get_full_hierarchy()
        print(f"Fetched {len(raw_hierarchy)} assets.")
        
        # 4. Process the raw data into a DataFrame
        df_hierarchy = process_hierarchy_to_dataframe(raw_hierarchy)
        print("Hierarchy DataFrame:")
        print(df_hierarchy.head())

        # Example: Get thresholds for the first measure point found
        mp_df = df_hierarchy[df_hierarchy['type'] == 'MP']
        if not mp_df.empty:
            first_mp_id = mp_df.iloc[0]['_id']
            first_mp_name = mp_df.iloc[0]['name']
            print(f"\nFetching thresholds for Measure Point: '{first_mp_name}' ({first_mp_id})")
            thresholds = client.get_thresholds(first_mp_id)
            print("Thresholds data:")
            print(json.dumps(thresholds, indent=2))
        
        # Example: Get network status
        print("\nFetching network status...")
        raw_network = client.get_network_status()
        df_network = process_network_status_to_dataframe(raw_network, df_hierarchy)
        print("Network Status DataFrame:")
        print(df_network.head())

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"\nAn error occurred: {e}")