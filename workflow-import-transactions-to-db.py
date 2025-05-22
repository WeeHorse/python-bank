from prefect import flow, task
import pandas as pd
from sqlalchemy import create_engine

@task
def import_csv_to_postgres(csv_path, table_name, db_url, column_mapping = None):
    # read the columns we want
    df = pd.read_csv(csv_path, usecols=column_mapping.keys())

    # drop dups
    df.drop_duplicates(subset=["Personnummer"], keep="first", inplace=True)

    # reset index
    df.reset_index(drop=True, inplace=True)

    engine = create_engine(db_url)
    if column_mapping:
        df.rename(columns=column_mapping, inplace=True)
    df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')

@flow
def load_data_flow():
    customers_mapping = { # Customer,Address,Phone,Personnummer,BankAccount
        "Customer": "name",
        "Personnummer": "ssn"
    }
    import_csv_to_postgres("data/sebank_customers_with_accounts.csv", "customers", "postgresql://postgres:postgres@localhost:5432/pythonbank", customers_mapping)

load_data_flow()
