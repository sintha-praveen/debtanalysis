import os
import pandas as pd
from sqlalchemy import create_engine

# ==========================================
# 1. PostgreSQL Connection Settings
# ==========================================
DB_USER = "postgres"
DB_PASSWORD = "admin"   # <-- Replace with your real PostgreSQL password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "international_debt_db"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ==========================================
# 2. Load Processed Cleaned Data
# ==========================================
PROCESSED_DIR = os.path.join("data", "processed")

print("Loading cleaned datasets...")
df_country = pd.read_csv(os.path.join(PROCESSED_DIR, "cleaned_IDS_CountryMetaData.csv"))
df_series = pd.read_csv(os.path.join(PROCESSED_DIR, "cleaned_IDS_SeriesMetaData.csv"))
df_long = pd.read_csv(os.path.join(PROCESSED_DIR, "cleaned_IDS_ALLCountries_Data_long.csv"))

# Normalize column names for SQL (replaces spaces/hyphens with underscores)
df_country.columns = df_country.columns.str.strip().str.replace(' ', '_').str.replace('-', '_').str.lower()
df_series.columns = df_series.columns.str.strip().str.replace(' ', '_').str.replace('-', '_').str.lower()
df_long.columns = df_long.columns.str.strip().str.replace(' ', '_').str.replace('-', '_').str.lower()

# ==========================================
# 3. Push Tables to PostgreSQL
# ==========================================

# 1. Countries Table
print("Pushing countries table...")
df_country.to_sql(
    "countries",
    engine,
    if_exists="replace",
    index=False
)

# 2. Indicators Table
print("Pushing indicators table...")
df_series.to_sql(
    "indicators",
    engine,
    if_exists="replace",
    index=False
)

# 3. Debt Data Table (Batched via chunksize for 1.5M+ rows)
print(f"Pushing debt_data table ({len(df_long):,} rows in chunks)...")
df_long.to_sql(
    "debt_data",
    engine,
    if_exists="replace",
    index=False,
    chunksize=5000,
    
    
)

print("✅ All 3 tables pushed to PostgreSQL successfully!")