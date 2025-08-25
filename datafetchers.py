#!python3
import pandas as pd
from config import DATA_DIR
import os

file_loc = DATA_DIR + "/transactions.csv"


def fetch_transaction_df_all() -> pd.DataFrame:
    df = pd.read_csv(file_loc)
    for col in df.columns:
        if col != "amount":
            df[col] = df[col].astype(str)
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M")
    return df


def fetch_csv_last_modified():
    return os.path.getmtime(file_loc)
