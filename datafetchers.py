#!python3

import sqlite3
import json
import datetime
import base64
import pandas as pd


dbfile = "../finances-data/plaid-sync.db"

interested_cols = [
    "amount",
    "date",
    "merchant_name",
    "name",
    "location.city",
    "location.region",
    "location.country",
    "personal_finance_category.primary",
    "personal_finance_category.detailed",
]


def fetch_transaction_df_by_daterange(
    start_date: datetime.date, end_date: datetime.date
) -> pd.DataFrame:
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    r = c.execute(
        """
        select plaid_json from transactions
        where json_extract(plaid_json, '$.date') between ? and ?
    """,
        (start_date, end_date),
    )
    jsons = [json.loads(d[0]) for d in r.fetchall()]
    return transform(pd.json_normalize(jsons))


def fetch_transaction_df_all() -> pd.DataFrame:
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    r = c.execute("select plaid_json from transactions")
    jsons = [json.loads(d[0]) for d in r.fetchall()]
    df = pd.json_normalize(jsons)
    # convert all non amount columns to str
    for col in df.columns:
        if col != "amount":
            df[col] = df[col].astype(str)
    return transform(df)


def transform(df) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M")
    df["Month_Name"] = df["date"].dt.strftime("%B %Y")
    aldirows = df.merchant_name == "Aldi"
    df.loc[aldirows, "personal_finance_category.primary"] = "GENERAL_MERCHANDISE"
    df.loc[aldirows, "personal_finance_category.detailed"] = (
        "GENERAL_MERCHANDISE_SUPERSTORES"
    )
    df = df[df.merchant_name != base64.b64decode("UGF0cmVvbg==").decode("utf-8")]
    return df


if __name__ == "__main__":
    print(fetch_transaction_df_all().columns)
