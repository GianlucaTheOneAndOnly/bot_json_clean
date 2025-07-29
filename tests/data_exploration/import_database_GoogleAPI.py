import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
import traceback
import os

# --- 1. Configuration ---
CREDENTIALS_FILE = 'config/google_credentials.json'
OUTPUT_DIR = 'data' # Dossier pour stocker les fichiers locaux

# Crée le dossier de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

sheetID = "1LI3DBTNkHiEWQXd99gd9E5-CZskY5DY_QOs10nE7x8M"

# --- 2. Fonction de récupération et de nettoyage ---
def get_sheet_as_dataframe(spreadsheet_id, sheet_name):
    """
    Se connecte à une Google Sheet, lit une feuille spécifique,
    et retourne les données sous forme de DataFrame pandas nettoyé.
    """
    print(f"\n--- Traitement de la feuille '{sheet_name}' de la spreadsheet ID '{spreadsheet_id}' ---")
    try:
        # Authentification (gspread gère la mise en cache des credentials)
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scopes)
        client = gspread.authorize(creds)
        
        # Ouverture et lecture
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        print(f"-> Lecture des données de '{spreadsheet.title}'...")
        
        data = worksheet.get_all_records(head=1)

    except Exception as e:
        print(f"ERREUR lors de la lecture de la feuille '{sheet_name}'.")
        traceback.print_exc()
        return None # Retourne None en cas d'erreur

    # --- Nettoyage du DataFrame ---
    if not data:
        print("-> La feuille est vide. Aucun DataFrame n'a été créé.")
        return None

    print("-> Formatage en DataFrame...")
    df = pd.DataFrame(data)
    df.replace('', np.nan, inplace=True)
    
    # Nettoyage spécifique (à adapter si les noms de colonnes changent)
    if 'Asset ID' in df.columns:
        df.dropna(subset=['Asset ID'], inplace=True)
    if 'Date Time' in df.columns:
        df['Date Time'] = pd.to_datetime(df['Date Time'], errors='coerce')
    
    print(f"-> Terminé. {len(df)} lignes valides trouvées.")
    return df

# --- 3. Utilisation de la fonction pour chaque Spreadsheet ---

# Dictionnaire de vos spreadsheets pour une gestion facile
spreadsheets_to_process = {
    "assets": {
        "id": sheetID,
        "sheet": "Asset"
    },
    "lookup": {
        "id": sheetID,
        "sheet": "Lookup"
    },
    "component": {
        "id": sheetID,
        "sheet": "Component"
    },
    "installation": {
        "id": sheetID,
        "sheet": "Installation"
    },
    "gateway": {
        "id": sheetID,
        "sheet": "Gateway"
    },
    "swap": {
        "id": sheetID,
        "sheet": "Swap"
    },
    "stock": {
        "id": sheetID,
        "sheet": "Stock"
    },
}

# Dictionnaire pour stocker les DataFrames obtenus
all_dataframes = {}

for name, info in spreadsheets_to_process.items():
    # Appelle la fonction pour chaque entrée
    df = get_sheet_as_dataframe(info["id"], info["sheet"])
    
    if df is not None:
        all_dataframes[name] = df
        
        # --- 4. Stockage en local au format CSV ---
        # Définir le chemin du fichier avec l'extension .csv
        file_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        try:
            # Sauvegarder en CSV avec un encodage adapté pour Excel
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"-> DataFrame '{name}' stocké avec succès dans '{file_path}'")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du fichier pour '{name}': {e}")


# --- 5. Accès aux DataFrames pour l'étude ---
print("\n--- Tous les DataFrames sont maintenant disponibles dans le dictionnaire 'all_dataframes' ---")