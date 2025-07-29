import pandas as pd
import os

# --- 1. Définir le chemin et charger les fichiers CSV ---
# Ajout de low_memory=False pour éviter les DtypeWarning
data_directory = 'data'
try:
    assets_df = pd.read_csv(os.path.join(data_directory, 'assets.csv'), low_memory=False)
    components_df = pd.read_csv(os.path.join(data_directory, 'component.csv'), low_memory=False)
    installation_df = pd.read_csv(os.path.join(data_directory, 'installation.csv'), low_memory=False)
    print("✅ Fichiers CSV chargés avec succès.")

except FileNotFoundError as e:
    print(f"❌ Erreur : Le fichier {e.filename} est introuvable.")
    exit() # Arrête le script si un fichier est manquant
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")
    exit()

# --- 2. Fusionner les DataFrames ---

# Étape 1: Fusionner 'assets' et 'components' sur 'Asset ID'
# On utilise une fusion "left" pour garder tous les actifs, même s'ils n'ont pas de composants.
# Les colonnes en double (sauf la clé) auront des suffixes _asset et _component.
merged_assets_components = pd.merge(
    assets_df,
    components_df,
    on='Asset ID',
    how='left',
    suffixes=('_asset', '_component')
)
print(f"\n📊 Après fusion de assets et components, le DataFrame a la forme : {merged_assets_components.shape}")


# Étape 2: Fusionner le résultat avec 'installation' sur 'Component ID'
# On utilise une fusion "left" pour garder tous les composants, même s'ils n'ont pas d'installation.
final_df = pd.merge(
    merged_assets_components,
    installation_df,
    on='Component ID',
    how='left',
    suffixes=('_comp', '_install') # Nouveaux suffixes pour d'éventuels doublons
)
print(f"📊 Après fusion avec installation, le DataFrame final a la forme : {final_df.shape}")


# --- 3. Afficher et sauvegarder le résultat ---

print("\n--- Aperçu du DataFrame final fusionné (5 premières lignes) ---")
print(final_df.head())

# Optionnel : Afficher toutes les colonnes pour vérifier les suffixes
print("\n--- Liste de toutes les colonnes du DataFrame final ---")
print(final_df.columns.tolist())

# Sauvegarder le résultat dans un nouveau fichier CSV pour une analyse plus approfondie
output_path = os.path.join(data_directory, 'merged_data.csv')
final_df.to_csv(output_path, index=False)

print(f"\n✅ Le DataFrame fusionné a été sauvegardé avec succès ici : {output_path}")

