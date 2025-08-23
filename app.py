from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import pathlib as pl
import dash_bootstrap_components as dbc
from datafetchers import fetch_transaction_df_all
from budget_progress_bars import create_budget_section

# Load data
# data_dir = pl.Path("statements")
# amex_dir = data_dir / "amex"
# amex_files = list(amex_dir.glob("*.csv"))

# df = pd.concat(
#     [pd.read_csv(file, parse_dates=["Date"]) for file in amex_files],
# )
df = fetch_transaction_df_all()
purchases_df = df[df.amount > 0]

# Setup Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

month_periods = df["Month"].sort_values().unique()
month_names = [df[df["Month"] == m]["Month_Name"].iloc[0] for m in month_periods]
max_month = month_names[-1]

CATEGORY_BUDGETS = {
    "GENERAL_MERCHANDISE": 600,
    "FOOD_AND_DRINK": 100,
    "TRANSPORTATION": 200,
    "Total": 2500,
}

category_to_color = {
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

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1("Finances", className="text-center my-4"), width=12)),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    options=[{"label": name, "value": name} for name in month_names]
                    + [{"label": "Last 30 Days", "value": "Last 30 Days"}],
                    value="Last 30 Days",
                    id="timespan-selection",
                    className="mb-4",
                ),
                width={"size": 6, "offset": 3},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.H1(id="total-spending-value", className="text-center mb-4"),
                width=12,
            )
        ),
        dbc.Row(dbc.Col(html.Div(id="budget-progress-section"), width=12)),
        dbc.Row(
            dbc.Col(
                html.H2("Spending Treemap", className="text-center mb-4"),
                width=12,
            )
        ),
        dbc.Row(dbc.Col(dcc.Graph(id="treemap-content"), width=12)),
        dbc.Row(
            dbc.Col(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                className="color-box",
                                                style={
                                                    "display": "inline-block",
                                                    "width": "20px",
                                                    "height": "20px",
                                                    "backgroundColor": color,
                                                    "marginRight": "8px",
                                                    "border": "1px solid #888",
                                                    "verticalAlign": "middle",
                                                },
                                            ),
                                            html.Span(
                                                category,
                                                style={"verticalAlign": "middle"},
                                            ),
                                        ],
                                        className="d-inline-block me-3 mb-2",
                                    )
                                    for category, color in category_to_color.items()
                                ],
                                className="text-center",
                            )
                        ],
                        className="mt-3",
                    )
                ]
            )
        ),
    ],
    fluid=True,
    className="px-4",
)


@callback(Output("treemap-content", "figure"), Input("timespan-selection", "value"))
def update_treemap(value):
    if value == "Last 30 Days":
        dff = purchases_df[
            purchases_df["date"] >= (pd.Timestamp.now() - pd.DateOffset(days=30))
        ]
    else:
        dff = purchases_df[purchases_df.Month_Name == value]
    chart = px.treemap(
        dff,
        path=["personal_finance_category.primary", "merchant_name"],
        values="amount",
        color="personal_finance_category.primary",
        color_discrete_map=category_to_color,
        hover_data=["name", "amount", "date"],
    )
    chart.update_traces(marker=dict(cornerradius=5), textfont_size=20)
    chart.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return chart


@callback(
    Output("total-spending-value", "children"), Input("timespan-selection", "value")
)
def update_total_spending(value):
    if value == "Last 30 Days":
        dff = purchases_df[
            purchases_df["date"] >= (pd.Timestamp.now() - pd.DateOffset(days=30))
        ]
    else:
        dff = purchases_df[purchases_df.Month_Name == value]
    total = dff["amount"].sum()
    return f"Total Spending: ${total:,.2f}"


@callback(
    Output("budget-progress-section", "children"), Input("timespan-selection", "value")
)
def update_budget_progress(value):
    if value == "Last 30 Days":
        dff = purchases_df[
            purchases_df["date"] >= (pd.Timestamp.now() - pd.DateOffset(days=30))
        ]
    else:
        dff = purchases_df[purchases_df.Month_Name == value]
    return create_budget_section(dff, CATEGORY_BUDGETS)


if __name__ == "__main__":
    app.run(debug=True)
