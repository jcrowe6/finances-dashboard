#!python3
import pandas as pd
from config import DATA_DIR
import os

maindata_loc = DATA_DIR + "/transactions.csv"
overrides_loc = DATA_DIR + "/overrides.csv"


def fetch_transaction_df_all() -> pd.DataFrame:
    df = pd.read_csv(maindata_loc)

    # Read overrides
    overrides_df = pd.read_csv(overrides_loc)

    # Create index on transaction_id for both dataframes
    df.set_index("transaction_id", inplace=True)
    overrides_df.set_index("transaction_id", inplace=True)

    # Update matching rows with override values
    df.update(overrides_df)

    # Reset index to make transaction_id a regular column again
    df.reset_index(inplace=True)

    for col in df.columns:
        if col != "amount":
            df[col] = df[col].astype(str)
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M")
    return df


def fetch_csv_last_modified():
    main_mod_time = os.path.getmtime(maindata_loc)
    overrides_mod_time = os.path.getmtime(overrides_loc)
    return max(main_mod_time, overrides_mod_time)
