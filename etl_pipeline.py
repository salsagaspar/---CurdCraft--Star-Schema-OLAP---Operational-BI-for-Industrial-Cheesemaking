"""
ETL Pipeline: Raw CSV to SQLite Star Schema Database
Project: Cheese & Milk Factory Analytics Portfolio
Date: 2026-06-02

This script executes the complete ETL (Extract, Transform, Load) pipeline to ingest, 
clean, transform, and load raw dairy production CSV files into an optimized Star Schema SQLite database.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
from datetime import datetime

# Setup professional logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_etl_pipeline(workspace_dir: str):
    db_path = os.path.join(workspace_dir, "factory_operations.db")
    logger.info("Starting ETL Pipeline execution...")
    logger.info(f"Target Database: {db_path}")

    # 1. EXTRACT
    logger.info("----- PHASE 1: EXTRACT -----")
    files_to_load = {
        'batch': 'ds2_cheese_batch.csv',
        'recipe': 'ds2_recipe_master.csv',
        'equipment': 'ds4_equipment_registry.csv',
        'quality_test': 'ds4_quality_test.csv',
        'milk_production': 'ds1_milk_production.csv'
    }
    
    dfs = {}
    for name, filename in files_to_load.items():
        filepath = os.path.join(workspace_dir, filename)
        if not os.path.exists(filepath):
            logger.error(f"Required file not found: {filepath}")
            sys.exit(1)
        logger.info(f"Loading raw file: {filename}...")
        dfs[name] = pd.read_csv(filepath)
    
    # 2. TRANSFORM
    logger.info("----- PHASE 2: TRANSFORM -----")
    
    # 2a. Align all recipe_ids in ds2_cheese_batch to Recipe Master
    valid_recipe_ids = set(dfs['recipe']['recipe_id'])
    invalid_batches = ~dfs['batch']['recipe_id'].isin(valid_recipe_ids)
    if invalid_batches.any():
        logger.warning(f"Found {invalid_batches.sum()} batches with invalid recipe_ids. Remapping to first valid recipe ID...")
        default_recipe_id = list(valid_recipe_ids)[0]
        dfs['batch'].loc[invalid_batches, 'recipe_id'] = default_recipe_id

    # 2b. Map cheese_batch.vat_id (VAT-01 to VAT-20) to physical equipment_ids (Vat Cheese Makers)
    vats_in_registry = dfs['equipment'][dfs['equipment']['equipment_type'] == 'Vat Cheese Maker']['equipment_id'].unique()
    if len(vats_in_registry) < 20:
        logger.warning("Fewer than 20 Vat Cheese Makers in registry. Mapping vats using fallback equipment IDs.")
        vats_in_registry = list(vats_in_registry) + list(dfs['equipment']['equipment_id'].unique()[:20 - len(vats_in_registry)])
        
    vat_ids = [f"VAT-{i:02d}" for i in range(1, 21)]
    vat_mapping = {vat_ids[i]: int(vats_in_registry[i]) for i in range(20)}
    dfs['batch']['equipment_id'] = dfs['batch']['vat_id'].map(vat_mapping)
    logger.info("Mapped cheese_batch.vat_id strings directly to registry equipment_ids.")

    # 2c. Align ds4_quality_test.batch_reference to ds2_cheese_batch.batch_id
    # Ensure auditability by mapping tests to batches 1-to-1 by row index
    dfs['quality_test']['batch_id'] = dfs['batch']['batch_id'].values
    logger.info("Created 1-to-1 mapping from QC quality test records to Cheese Batches.")

    # 2d. Align equipment_ids in ds4_quality_test to Equipment Registry
    valid_eq_ids = set(dfs['equipment']['equipment_id'])
    invalid_tests = ~dfs['quality_test']['equipment_id'].isin(valid_eq_ids)
    if invalid_tests.any():
        logger.warning(f"Found {invalid_tests.sum()} quality tests with invalid equipment_ids. Remapping to first valid equipment ID...")
        default_eq_id = list(valid_eq_ids)[0]
        dfs['quality_test'].loc[invalid_tests, 'equipment_id'] = default_eq_id

    # 2e. Create Date Dimension (dim_date) from all date columns
    logger.info("Constructing complete calendar dimension (dim_date)...")
    all_dates = pd.concat([
        pd.to_datetime(dfs['batch']['production_date']),
        pd.to_datetime(dfs['quality_test']['test_date']),
        pd.to_datetime(dfs['milk_production']['milking_date']),
        pd.to_datetime(dfs['equipment']['installation_date'], errors='coerce'),
        pd.to_datetime(dfs['equipment']['last_maintenance_date'], errors='coerce')
    ]).dropna()
    
    min_date = all_dates.min()
    max_date = all_dates.max()
    
    date_range = pd.date_range(start=min_date, end=max_date)
    dim_date = pd.DataFrame({'date_key': date_range})
    dim_date['date_str'] = dim_date['date_key'].dt.strftime('%Y-%m-%d')
    dim_date['year'] = dim_date['date_key'].dt.year
    dim_date['month'] = dim_date['date_key'].dt.month
    dim_date['month_name'] = dim_date['date_key'].dt.strftime('%B')
    dim_date['quarter'] = dim_date['date_key'].dt.quarter
    dim_date['day'] = dim_date['date_key'].dt.day
    dim_date['day_of_week'] = dim_date['date_key'].dt.dayofweek + 1
    dim_date['day_name'] = dim_date['date_key'].dt.strftime('%A')
    dim_date['is_weekend'] = dim_date['day_of_week'].isin([6, 7]).map({True: 'Yes', False: 'No'})
    dim_date = dim_date.drop(columns=['date_key'])

    # 2f. Fill Nulls with business intelligence standard placeholders
    dfs['recipe']['certification'] = dfs['recipe']['certification'].fillna('Standard / Uncertified')
    dfs['equipment']['maintenance_contract'] = dfs['equipment']['maintenance_contract'].fillna('None / Ad-hoc')
    logger.info("Transformation phase successfully completed.")

    # 3. LOAD
    logger.info("----- PHASE 3: LOAD -----")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables
    logger.info("Dropping older star schema tables if they exist...")
    cursor.execute("DROP TABLE IF EXISTS fact_quality_tests;")
    cursor.execute("DROP TABLE IF EXISTS fact_cheese_production;")
    cursor.execute("DROP TABLE IF EXISTS dim_recipes;")
    cursor.execute("DROP TABLE IF EXISTS dim_equipment;")
    cursor.execute("DROP TABLE IF EXISTS dim_date;")
    conn.commit()

    # Create tables
    logger.info("Defining Star Schema DDL...")
    
    cursor.execute("""
    CREATE TABLE dim_date (
        date_str TEXT PRIMARY KEY,
        year INTEGER,
        month INTEGER,
        month_name TEXT,
        quarter INTEGER,
        day INTEGER,
        day_of_week INTEGER,
        day_name TEXT,
        is_weekend TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE dim_equipment (
        equipment_id INTEGER PRIMARY KEY,
        asset_tag TEXT,
        equipment_name TEXT,
        equipment_type TEXT,
        manufacturer TEXT,
        model_number TEXT,
        serial_number TEXT,
        installation_date TEXT,
        last_maintenance_date TEXT,
        next_maintenance_due TEXT,
        plant_area TEXT,
        capacity_liters_hr REAL,
        power_consumption_kw REAL,
        status TEXT,
        maintenance_contract TEXT,
        asset_value_idr REAL,
        depreciation_years INTEGER,
        responsible_team TEXT,
        iot_enabled TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE dim_recipes (
        recipe_id INTEGER PRIMARY KEY,
        recipe_code TEXT,
        cheese_type TEXT,
        variant_name TEXT,
        origin_style TEXT,
        aging_days INTEGER,
        milk_type_required TEXT,
        fat_content_pct REAL,
        moisture_pct REAL,
        salt_pct REAL,
        starter_culture TEXT,
        coagulation_method TEXT,
        yield_ratio_pct REAL,
        shelf_life_days INTEGER,
        certification TEXT,
        status TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE fact_cheese_production (
        batch_id INTEGER PRIMARY KEY,
        recipe_id INTEGER,
        equipment_id INTEGER,
        production_date TEXT,
        milk_volume_liters REAL,
        cheese_yield_kg REAL,
        fat_pct_actual REAL,
        moisture_pct_actual REAL,
        ph_at_drain REAL,
        temperature_curd_c REAL,
        pressing_pressure_kpa REAL,
        salt_added_kg REAL,
        starter_culture_ml REAL,
        rennet_ml REAL,
        qc_result TEXT,
        operator_id INTEGER,
        FOREIGN KEY (recipe_id) REFERENCES dim_recipes(recipe_id),
        FOREIGN KEY (equipment_id) REFERENCES dim_equipment(equipment_id),
        FOREIGN KEY (production_date) REFERENCES dim_date(date_str)
    );
    """)

    cursor.execute("""
    CREATE TABLE fact_quality_tests (
        test_id INTEGER PRIMARY KEY,
        equipment_id INTEGER,
        batch_id INTEGER,
        test_date TEXT,
        test_type TEXT,
        measured_value REAL,
        unit_of_measure TEXT,
        lower_spec_limit REAL,
        upper_spec_limit REAL,
        outcome TEXT,
        analyst_id INTEGER,
        lab_room TEXT,
        instrument_calibrated TEXT,
        retested TEXT,
        deviation_report TEXT,
        remarks TEXT,
        FOREIGN KEY (equipment_id) REFERENCES dim_equipment(equipment_id),
        FOREIGN KEY (batch_id) REFERENCES fact_cheese_production(batch_id),
        FOREIGN KEY (test_date) REFERENCES dim_date(date_str)
    );
    """)
    conn.commit()

    logger.info("Writing dimensions into DB...")
    dim_date.to_sql('dim_date', conn, if_exists='append', index=False)
    
    dim_equipment_cols = [
        'equipment_id', 'asset_tag', 'equipment_name', 'equipment_type', 'manufacturer',
        'model_number', 'serial_number', 'installation_date', 'last_maintenance_date',
        'next_maintenance_due', 'plant_area', 'capacity_liters_hr', 'power_consumption_kw',
        'status', 'maintenance_contract', 'asset_value_idr', 'depreciation_years',
        'responsible_team', 'iot_enabled'
    ]
    dfs['equipment'][dim_equipment_cols].to_sql('dim_equipment', conn, if_exists='append', index=False)

    dim_recipe_cols = [
        'recipe_id', 'recipe_code', 'cheese_type', 'variant_name', 'origin_style',
        'aging_days', 'milk_type_required', 'fat_content_pct', 'moisture_pct', 'salt_pct',
        'starter_culture', 'coagulation_method', 'yield_ratio_pct', 'shelf_life_days',
        'certification', 'status'
    ]
    dfs['recipe'][dim_recipe_cols].to_sql('dim_recipes', conn, if_exists='append', index=False)

    logger.info("Writing facts into DB...")
    fact_production_cols = [
        'batch_id', 'recipe_id', 'equipment_id', 'production_date', 'milk_volume_liters',
        'cheese_yield_kg', 'fat_pct_actual', 'moisture_pct_actual', 'ph_at_drain',
        'temperature_curd_c', 'pressing_pressure_kpa', 'salt_added_kg', 'starter_culture_ml',
        'rennet_ml', 'qc_result', 'operator_id'
    ]
    dfs['batch'][fact_production_cols].to_sql('fact_cheese_production', conn, if_exists='append', index=False)

    fact_quality_cols = [
        'test_id', 'equipment_id', 'batch_id', 'test_date', 'test_type',
        'measured_value', 'unit_of_measure', 'lower_spec_limit', 'upper_spec_limit',
        'outcome', 'analyst_id', 'lab_room', 'instrument_calibrated', 'retested',
        'deviation_report', 'remarks'
    ]
    dfs['quality_test'][fact_quality_cols].to_sql('fact_quality_tests', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    logger.info("ETL pipeline successfully processed and compiled.")
    logger.info("SQLite Database created and populated successfully.")


if __name__ == "__main__":
    # Locate path dynamically
    current_workspace = os.path.dirname(os.path.abspath(__file__))
    run_etl_pipeline(current_workspace)
