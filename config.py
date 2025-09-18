import os

SECRET_KEY = os.environ.get("SECRET_KEY")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD")
DATA_DIR = os.environ.get("DATA_DIR")

CATEGORY_BUDGETS = {
    "Total": 2500,
    "GENERAL_MERCHANDISE": 600,
    "FOOD_AND_DRINK": 100,
    "TRANSPORTATION": 200,
}

INDIVIDUAL_BUDGETS = {"Extras": 100}

CATEGORY_COLOR = {
    "GENERAL_SERVICES": "lightgreen",
    "RENT_AND_UTILITIES": "plum",
    "LOAN_PAYMENTS": "lightblue",
    "GENERAL_MERCHANDISE": "lightblue",
    "FOOD_AND_DRINK": "orange",
    "TRANSPORTATION": "lightcoral",
    "ENTERTAINMENT": "gold",
    "TRANSFER_OUT": "pink",
    "PERSONAL_CARE": "lightpink",
    "MEDICAL": "hotpink",
    "BANK_FEES": "lightgray",
    "GOVERNMENT_AND_NON_PROFIT": "lightcyan",
    "HOME_IMPROVEMENT": "lightsalmon",
}

NON_EXTRA_CATEGORIES = [
    "GENERAL_MERCHANDISE",
    "FOOD_AND_DRINK",
    "TRANSPORTATION",
    "RENT_AND_UTILITIES",
    "MEDICAL",
]

TRANSACTIONS_TABLE_PAGE_SIZE = 10
