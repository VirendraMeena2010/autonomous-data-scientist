import os
import dlt
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series
import duckdb

# ==========================================
# PHASE 1: DATA INGESTION (dlt)
# ==========================================
# dlt extracts data raw from sources without loading everything into memory.
# For demonstration, we ingest mock user transactional data simulating an API response.

@dlt.resource(name="raw_transactions", write_disposition="replace")
def fetch_api_data():
    """Simulates streaming or paginated API data ingestion."""
    mock_api_response = [
        {"user_id": 101, "signup_date": "2026-01-15", "purchase_amount": 250.50, "status": "active"},
        {"user_id": 102, "signup_date": "2026-02-20", "purchase_amount": 99.99, "status": "active"},
        {"user_id": 103, "signup_date": "2026-03-05", "purchase_amount": 0.00, "status": "inactive"},
        {"user_id": 104, "signup_date": "2026-03-12", "purchase_amount": 1250.00, "status": "active"},
    ]
    for record in mock_api_response:
        yield record

def run_ingestion_pipeline() -> str:
    """Runs the dlt pipeline targeting a local DuckDB instance."""
    pipeline = dlt.pipeline(
        pipeline_name="api_ingestion",
        destination="duckdb",
        dataset_name="staging"
    )
    # Extracts from API generator and writes directly to raw staging database
    load_info = pipeline.run(fetch_api_data())
    return pipeline.dataset_name

# ==========================================
# PHASE 2: DATA VALIDATION (Pandera)
# ==========================================
# Before running transformations, we enforce strict type and constraint checks.

class TransactionSchema(pa.DataFrameModel):
    """Defines strict types and business constraints for incoming staging data."""
    user_id: Series[int] = pa.Field(unique=True)
    signup_date: Series[str] = pa.Field(nullable=False)
    # Validate that purchase amounts cannot be negative values
    purchase_amount: Series[float] = pa.Field(ge=0.0) 
    status: Series[str] = pa.Field(isin=["active", "inactive"])

    class Config:
        coerce = True # Automatically attempts type casting during validation

def validate_staging_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validates the extracted pandas DataFrame against the Pandera Schema."""
    try:
        validated_df = TransactionSchema.validate(df)
        print("✅ Data validation passed successfully.")
        return validated_df
    except pa.errors.SchemaErrors as err:
        print("❌ Data validation failed. Schema errors detected:")
        print(err.failure_cases)
        raise err

# ==========================================
# PHASE 3: DATA MANIPULATION (Pandas)
# ==========================================
# Cleans, joins, and aggregates the validated transactional data.

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans up types, calculates a user classification column, and filters fields."""
    # Convert string dates to datetime objects
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    
    # Feature engineering: Segment users by purchase value
    df["tier"] = df["purchase_amount"].apply(
        lambda x: "VIP" if x >= 500 else ("Standard" if x > 0 else "Free")
    )
    
    # Filter for active users only
    transformed_df = df[df["status"] == "active"].copy()
    return transformed_df

# ==========================================
# PHASE 4: MAIN RUNNER & ANALYTICS ENGINE (DuckDB)
# ==========================================
def main():
    DB_PATH = "api_ingestion.duckdb"
    
    print("--- Starting Pipeline ---")
    
    # 1. Ingest Data using dlt
    staging_dataset = run_ingestion_pipeline()
    print(f"1. Ingestion Complete. Data landed in staging dataset.")

    # Connect to the DuckDB instance populated by dlt
    con = duckdb.connect(DB_PATH)
    
    # 2. Pull raw data out into Pandas for schema enforcement
    raw_df = con.execute(f"SELECT * FROM {staging_dataset}.raw_transactions").df()
    
    # 3. Validate Data using Pandera
    validated_df = validate_staging_data(raw_df)
    
    # 4. Transform Data using Pandas
    curated_df = transform_data(validated_df)
    print("3. Data transformation complete.")
    
    # Register the pandas DataFrame as a virtual view inside DuckDB for fast SQL queries
    con.register("v_curated_transactions", curated_df)
    
    # 5. Fast SQL Analytics using DuckDB
    # Calculate financial summaries directly inside memory via SQL
    print("\n--- Analytics Report (DuckDB SQL Engine) ---")
    analytics_query = """
        SELECT 
            tier,
            COUNT(user_id) as total_users,
            SUM(purchase_amount) as total_revenue,
            AVG(purchase_amount) as average_ticket_size
        FROM v_curated_transactions
        GROUP BY tier
        ORDER BY total_revenue DESC;
    """
    
    report_df = con.execute(analytics_query).df()
    print(report_df.to_string(index=False))
    
    con.close()

if __name__ == "__main__":
    main()
