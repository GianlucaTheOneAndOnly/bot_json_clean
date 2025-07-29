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
merged_assets_components = pd.merge(
    assets_df,
    components_df,
    on='Asset ID',
    how='left',
    suffixes=('_asset', '_component')
)
print(f"\n📊 Après fusion de assets et components, le DataFrame a la forme : {merged_assets_components.shape}")

# Étape 2: Fusionner le résultat avec 'installation' sur 'Component ID'
# Cette fusion est correcte, même si elle crée beaucoup de lignes, car elle reflète une relation un-à-plusieurs.
final_df = pd.merge(
    merged_assets_components,
    installation_df,
    on='Component ID',
    how='left',
    suffixes=('_comp', '_install')
)
print(f"📊 Après fusion avec installation, le DataFrame final a la forme : {final_df.shape}")


# --- 3. Afficher et sauvegarder le résultat ---

print("\n--- Aperçu du DataFrame final fusionné (5 premières lignes) ---")
print(final_df.head())

# --- 4. Vérification des duplications dans le DataFrame final ---

print("\n--- Analyse des duplications (pour confirmer les relations un-à-plusieurs) ---")

# Fonction pour vérifier et afficher les doublons pour une colonne donnée
def check_duplicates(df, column_name):
    print(f"\n🔎 Vérification des duplications pour '{column_name}'...")
    duplicates = df[df[column_name].notna() & df[column_name].duplicated(keep=False)]
    
    if duplicates.empty:
        print(f"✅ Aucune duplication trouvée pour '{column_name}'.")
    else:
        print(f"⚠️ {len(duplicates)} lignes sont concernées par des duplications sur '{column_name}'.")
        duplicate_counts = duplicates[column_name].value_counts()
        print(f"Nombre d'éléments par ID dupliqué (Top 5) :")
        print(duplicate_counts.head())
        
if 'Component ID' in final_df.columns:
    check_duplicates(final_df, 'Component ID')


# --- 5. NOUVEAU : Analyse détaillée d'un composant avec plusieurs installations ---
print("\n--- Analyse détaillée d'un composant avec plusieurs installations ---")
# On prend un exemple parmi les plus dupliqués de la sortie précédente pour comprendre ce qui différencie les lignes.
# Remplacez cette valeur si nécessaire par un autre ID de votre sortie.
example_component_id = 'PUMP_8cd3ced3' 
print(f"Affichage des installations pour le Component ID : '{example_component_id}'\n")

# Filtrer le dataframe final pour ce composant spécifique
component_details = final_df[final_df['Component ID'] == example_component_id].copy()

if component_details.empty:
    print(f"L'ID d'exemple '{example_component_id}' n'a pas été trouvé. Choisissez-en un depuis la sortie de l'analyse des duplications ci-dessus.")
else:
    # Sélectionner les colonnes les plus pertinentes de la partie 'installation' pour voir ce qui les différencie
    cols_to_inspect = [
        'Map ID',
        'Component ID', 
        'Installation ID', 
        'Date Time', # La date de l'installation
        'User', 
        'Pin_install',
        'Serial Number', 
        'Status',
        'DE or NDE'
    ]
    # S'assurer que les colonnes existent avant de les utiliser pour éviter une erreur
    existing_cols_to_inspect = [col for col in cols_to_inspect if col in component_details.columns]
    
    # Convertir les colonnes de date en format lisible si elles ne le sont pas déjà
    if 'Date Time' in existing_cols_to_inspect:
        component_details['Date Time'] = pd.to_datetime(component_details['Date Time'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

    print("En regardant ce tableau, cherchez ce qui change d'une ligne à l'autre : est-ce l'Installation ID, le Pin, le Status ?")
    print(component_details[existing_cols_to_inspect].to_string())


# --- 6. Sauvegarde du fichier final ---
output_path = os.path.join(data_directory, 'merged_data.csv')
final_df.to_csv(output_path, index=False)

print(f"\n\n✅ Le DataFrame fusionné a été sauvegardé avec succès ici : {output_path}")
