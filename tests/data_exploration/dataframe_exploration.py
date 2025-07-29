import pandas as pd
import os

# --- 1. Définir le chemin vers le dossier contenant les fichiers CSV ---
# Le code suppose que vos fichiers se trouvent dans un sous-dossier nommé 'data'
data_directory = 'data'

# --- 2. Lire les fichiers CSV dans des DataFrames pandas ---
try:
    assets_df = pd.read_csv(os.path.join(data_directory, 'assets.csv'))
    components_df = pd.read_csv(os.path.join(data_directory, 'component.csv'))
    installation_df = pd.read_csv(os.path.join(data_directory, 'installation.csv'))

    print("✅ Fichiers CSV chargés avec succès.")

    # --- 3. Extraire et afficher les en-têtes de chaque DataFrame ---
    assets_headers = set(assets_df.columns)
    components_headers = set(components_df.columns)
    installation_headers = set(installation_df.columns)

    print("\n--- En-têtes des fichiers ---")
    print(f"Colonnes de 'assets.csv': {sorted(list(assets_headers))}")
    print(f"Colonnes de 'component.csv': {sorted(list(components_headers))}")
    print(f"Colonnes de 'installation.csv': {sorted(list(installation_headers))}")

    # --- 4. Comparer les en-têtes pour trouver les colonnes communes ---
    common_assets_components = assets_headers.intersection(components_headers)
    common_assets_installation = assets_headers.intersection(installation_headers)
    common_components_installation = components_headers.intersection(installation_headers)
    common_all = assets_headers.intersection(components_headers, installation_headers)

    print("\n--- Analyse des clés de jonction potentielles ---")
    if common_all:
        print(f"🔑 Colonnes communes aux 3 fichiers : {list(common_all)}")
    else:
        print("ℹ️ Aucune colonne n'est commune aux trois fichiers.")

    if common_assets_components:
        print(f"🔗 Colonnes communes entre 'assets' et 'components' : {list(common_assets_components)}")

    if common_assets_installation:
        print(f"🔗 Colonnes communes entre 'assets' et 'installation' : {list(common_assets_installation)}")

    if common_components_installation:
        print(f"🔗 Colonnes communes entre 'components' et 'installation' : {list(common_components_installation)}")

except FileNotFoundError as e:
    print(f"❌ Erreur : Le fichier {e.filename} est introuvable. Veuillez vérifier que le nom du fichier et le chemin d'accès sont corrects.")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")