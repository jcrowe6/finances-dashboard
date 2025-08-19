from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import pathlib as pl
import dash_bootstrap_components as dbc

# Load data
data_dir = pl.Path("statements")
amex_dir = data_dir / "amex"
amex_files = list(amex_dir.glob("*.csv"))

amex_df = pd.concat(
    [pd.read_csv(file, parse_dates=["Date"]) for file in amex_files],
)
amex_df["Month"] = amex_df["Date"].dt.to_period("M")
amex_df["Month_Name"] = amex_df["Date"].dt.strftime("%B %Y")
amex_df["Category_1"] = amex_df["Category"].str.split("-").str[0]
amex_df["Category_2"] = amex_df["Category"].str.split("-").str[1]
amex_df["Simple_Desc"] = amex_df["Description"].str.split(" ").str[:2].str.join(" ")
amex_df = amex_df[amex_df["Amount"] > 0]

# Setup Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

month_periods = amex_df["Month"].sort_values().unique()
month_names = [
    amex_df[amex_df["Month"] == m]["Month_Name"].iloc[0] for m in month_periods
]
max_month = month_names[-1]

category_to_color = {
    "Merchandise & Supplies": "lightblue",
    "Business Services": "lightgreen",
    "Transportation": "lightcoral",
    "Communications": "plum",
    "Restaurant": "orange",
    "Fees & Adjustments": "tan",
    "Travel": "pink",
    "Entertainment": "gold",
    "Other": "gray",
}

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1("Finances", className="text-center my-4"), width=12)),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    options=[{"label": name, "value": name} for name in month_names],
                    value=max_month,
                    id="month-selection",
                    className="mb-4",
                ),
                width={"size": 6, "offset": 3},
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


@callback(Output("treemap-content", "figure"), Input("month-selection", "value"))
def update_treemap(value):
    dff = amex_df[amex_df.Month_Name == value]
    chart = px.treemap(
        dff,
        path=["Category_2", "Simple_Desc"],
        values="Amount",
        color="Category_1",
        color_discrete_map=category_to_color,
        hover_data=["Amount", "Description", "Date"],
    )
    chart.update_traces(marker=dict(cornerradius=5), textfont_size=20)
    chart.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return chart


if __name__ == "__main__":
    app.run(debug=True)
