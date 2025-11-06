#!/usr/bin/env python
"""
PySpark Script to Transform Django Banking System Data

This script reads data from the Django banking system's SQLite database
and transforms it into Spark DataFrames. It supports multiple output formats:
console display, Parquet, and CSV.

Usage:
    python spark_transform.py --output console       # Display DataFrames
    python spark_transform.py --output parquet       # Save as Parquet files
    python spark_transform.py --output csv           # Save as CSV files
    python spark_transform.py --tables users transactions  # Process specific tables

Examples:
    python create_demo_data.py
    
    python spark_transform.py --output console
    
    python spark_transform.py --output parquet
    
    python spark_transform.py --output csv --tables users transactions
"""

import argparse
import os
import sys
import sqlite3
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    LongType, BooleanType, DecimalType, TimestampType
)


TRANSACTION_TYPE_MAPPING = {
    1: 'Deposit',
    2: 'Withdrawal',
    3: 'Interest'
}

TABLE_SCHEMAS = {
    'accounts_user': StructType([
        StructField('id', LongType(), False),
        StructField('password', StringType(), False),
        StructField('last_login', StringType(), True),
        StructField('is_superuser', StringType(), False),
        StructField('first_name', StringType(), False),
        StructField('last_name', StringType(), False),
        StructField('is_staff', StringType(), False),
        StructField('is_active', StringType(), False),
        StructField('date_joined', StringType(), False),
        StructField('email', StringType(), False),
    ]),
    'accounts_bankaccounttype': StructType([
        StructField('id', LongType(), False),
        StructField('name', StringType(), False),
        StructField('maximum_withdrawal_amount', StringType(), False),
        StructField('annual_interest_rate', StringType(), False),
        StructField('interest_calculation_per_year', LongType(), False),
    ]),
    'accounts_userbankaccount': StructType([
        StructField('id', LongType(), False),
        StructField('account_no', LongType(), False),
        StructField('gender', StringType(), False),
        StructField('birth_date', StringType(), True),
        StructField('balance', StringType(), False),
        StructField('interest_start_date', StringType(), True),
        StructField('initial_deposit_date', StringType(), True),
        StructField('account_type_id', LongType(), False),
        StructField('user_id', LongType(), False),
    ]),
    'accounts_useraddress': StructType([
        StructField('id', LongType(), False),
        StructField('street_address', StringType(), False),
        StructField('city', StringType(), False),
        StructField('postal_code', LongType(), False),
        StructField('country', StringType(), False),
        StructField('user_id', LongType(), False),
    ]),
    'transactions_transaction': StructType([
        StructField('id', LongType(), False),
        StructField('amount', StringType(), False),
        StructField('balance_after_transaction', StringType(), False),
        StructField('transaction_type', LongType(), False),
        StructField('timestamp', StringType(), False),
        StructField('account_id', LongType(), False),
    ]),
}

TABLE_CONFIGS = {
    'users': {
        'table_name': 'accounts_user',
        'output_name': 'users',
        'description': 'User accounts with authentication'
    },
    'bank_account_types': {
        'table_name': 'accounts_bankaccounttype',
        'output_name': 'bank_account_types',
        'description': 'Bank account types with interest rates'
    },
    'user_bank_accounts': {
        'table_name': 'accounts_userbankaccount',
        'output_name': 'user_bank_accounts',
        'description': 'User bank accounts with balances'
    },
    'user_addresses': {
        'table_name': 'accounts_useraddress',
        'output_name': 'user_addresses',
        'description': 'User addresses'
    },
    'transactions': {
        'table_name': 'transactions_transaction',
        'output_name': 'transactions',
        'description': 'Financial transactions'
    }
}


def create_spark_session(app_name='BankingSystemDataTransform'):
    """Create and return a SparkSession."""
    try:
        spark = SparkSession.builder \
            .appName(app_name) \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        
        return spark
    except Exception as e:
        print(f"Error creating Spark session: {e}")
        sys.exit(1)


def get_database_path():
    """Get the absolute path to the SQLite database."""
    db_path = Path(__file__).parent / 'db.sqlite3'
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run 'python create_demo_data.py' first to create demo data.")
        sys.exit(1)
    
    return str(db_path.absolute())


def read_table_from_sqlite(spark, db_path, table_name):
    """Read a table from SQLite database into a Spark DataFrame.
    
    Uses sqlite3 directly to read data with explicit schemas to avoid type inference issues.
    """
    try:
        schema = TABLE_SCHEMAS.get(table_name)
        if not schema:
            print(f"Error: No schema defined for table {table_name}")
            return None
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        conn.close()
        
        if not rows:
            print(f"Warning: Table {table_name} is empty")
            return spark.createDataFrame([], schema=schema)
        
        df = spark.createDataFrame(rows, schema=schema)
        
        return df
    except Exception as e:
        print(f"Error reading table {table_name}: {e}")
        return None


def add_transaction_type_labels(df):
    """Add human-readable transaction type labels to the transactions DataFrame."""
    transaction_type_expr = when(col("transaction_type") == 1, "Deposit") \
        .when(col("transaction_type") == 2, "Withdrawal") \
        .when(col("transaction_type") == 3, "Interest") \
        .otherwise("Unknown")
    
    df = df.withColumn("transaction_type_label", transaction_type_expr)
    
    return df


def display_dataframe(df, table_key, config):
    """Display a DataFrame to the console with formatting."""
    print(f"\n{'='*80}")
    print(f"Table: {config['output_name']}")
    print(f"Description: {config['description']}")
    print(f"Rows: {df.count()}")
    print(f"{'='*80}")
    df.show(truncate=False)
    print(f"\nSchema for {config['output_name']}:")
    df.printSchema()


def save_as_parquet(df, table_key, config, output_dir='data'):
    """Save a DataFrame as Parquet format."""
    output_path = Path(output_dir) / f"{config['output_name']}.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.write.mode('overwrite').parquet(str(output_path))
        print(f"✓ Saved {config['output_name']} to {output_path} ({df.count()} rows)")
    except Exception as e:
        print(f"✗ Error saving {config['output_name']} as Parquet: {e}")


def save_as_csv(df, table_key, config, output_dir='data'):
    """Save a DataFrame as CSV format."""
    output_path = Path(output_dir) / f"{config['output_name']}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.coalesce(1).write.mode('overwrite') \
            .option('header', 'true') \
            .csv(str(output_path))
        print(f"✓ Saved {config['output_name']} to {output_path} ({df.count()} rows)")
    except Exception as e:
        print(f"✗ Error saving {config['output_name']} as CSV: {e}")


def process_tables(spark, db_path, output_format, tables_filter=None):
    """Process all or selected tables based on the specified output format."""
    tables_to_process = TABLE_CONFIGS.keys() if tables_filter is None else tables_filter
    
    print(f"\n🔄 Processing tables with output format: {output_format}")
    print(f"Database: {db_path}")
    print(f"Tables: {', '.join(tables_to_process)}\n")
    
    for table_key in tables_to_process:
        if table_key not in TABLE_CONFIGS:
            print(f"⚠ Warning: Unknown table '{table_key}', skipping...")
            continue
        
        config = TABLE_CONFIGS[table_key]
        table_name = config['table_name']
        
        df = read_table_from_sqlite(spark, db_path, table_name)
        
        if df is None:
            print(f"✗ Failed to read table: {table_name}")
            continue
        
        if table_key == 'transactions':
            df = add_transaction_type_labels(df)
        
        if output_format == 'console':
            display_dataframe(df, table_key, config)
        elif output_format == 'parquet':
            save_as_parquet(df, table_key, config)
        elif output_format == 'csv':
            save_as_csv(df, table_key, config)
    
    if output_format != 'console':
        print(f"\n✅ All tables processed successfully!")
        print(f"Output directory: {Path('data').absolute()}")


def main():
    """Main function to parse arguments and execute the transformation."""
    parser = argparse.ArgumentParser(
        description='Transform Django banking system data using PySpark',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--output',
        choices=['console', 'parquet', 'csv'],
        default='console',
        help='Output format: console (display), parquet, or csv (default: console)'
    )
    
    parser.add_argument(
        '--tables',
        nargs='+',
        choices=list(TABLE_CONFIGS.keys()),
        help='Specific tables to process (default: all tables)'
    )
    
    parser.add_argument(
        '--list-tables',
        action='store_true',
        help='List available tables and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_tables:
        print("\nAvailable tables:")
        for key, config in TABLE_CONFIGS.items():
            print(f"  - {key:20} : {config['description']}")
        return
    
    db_path = get_database_path()
    
    spark = create_spark_session()
    
    try:
        process_tables(spark, db_path, args.output, args.tables)
    finally:
        spark.stop()
        print("\n✅ Spark session closed.")


if __name__ == '__main__':
    main()
