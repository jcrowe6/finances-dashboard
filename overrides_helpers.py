import pandas as pd
from typing import Optional
from config import MAIN_DATA_LOC, OVERRIDES_LOC


def get_maindata_row_by_transaction_id(transaction_id) -> pd.Series:
    df = pd.read_csv(MAIN_DATA_LOC)
    row = df[df["transaction_id"] == transaction_id]
    return row


def read_overrides() -> pd.DataFrame:
    return pd.read_csv(OVERRIDES_LOC)


def upsert_override(
    transaction_id: str,
    new_amount: Optional[float] = None,
    new_category: Optional[str] = None,
) -> None:
    """Possibly add then update an override for a specific transaction"""
    overrides_df = read_overrides()

    # Check if the transaction_id already exists
    if transaction_id not in overrides_df["transaction_id"].values:
        # Add new override as copy from main data
        new_row = get_maindata_row_by_transaction_id(transaction_id)
        print(new_row)
        overrides_df = pd.concat([overrides_df, pd.DataFrame(new_row)])

    if new_amount is not None:
        overrides_df.loc[overrides_df["transaction_id"] == transaction_id, "amount"] = (
            new_amount
        )

    if new_category is not None:
        overrides_df.loc[
            overrides_df["transaction_id"] == transaction_id, "category"
        ] = new_category

    print(overrides_df)
    # Save back to CSV
    overrides_df.to_csv(OVERRIDES_LOC, index=False)
