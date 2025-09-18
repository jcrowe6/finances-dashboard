from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from datafetchers import fetch_transaction_df_all, fetch_csv_last_modified
from budget_progress_bars import create_budget_section
from config import (
    INDIVIDUAL_BUDGETS,
    CATEGORY_BUDGETS,
    CATEGORY_COLOR,
    NON_EXTRA_CATEGORIES,
    TRANSACTIONS_TABLE_PAGE_SIZE,
)
import numpy as np


class FinanceDashboard:
    def __init__(self, server):
        self.server = server
        self.category_budgets = CATEGORY_BUDGETS
        self.individual_budgets = INDIVIDUAL_BUDGETS
        self.category_colors = CATEGORY_COLOR

        # Not necessary but just as a reminder these values get set on data fetch
        self.df = None
        self.purchases_df = None
        self.month_names = None
        self.max_month = None
        self.last_updated = None
        # This one is necessary as it gets checked against the file mod time
        self.last_modified = 0
        # Set them
        self.get_and_set_data_if_new()

        # This will hold the filtered dataframe. Also not necessary to define right now
        self.dff = None

        # Initialize Dash app with enhanced styling
        self.app = Dash(
            __name__,
            server=server,
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
            ],
            url_base_pathname="/",
        )

        # Add custom CSS
        self.app.index_string = """
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        margin: 0;
                    }
                    
                    .main-container {
                        background: rgba(255, 255, 255, 0.95);
                        backdrop-filter: blur(10px);
                        border-radius: 20px;
                        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                        margin: 20px;
                        min-height: calc(100vh - 40px);
                    }
                    
                    .dashboard-header {
                        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
                        color: white;
                        border-radius: 20px 20px 0 0;
                        padding: 2rem;
                        text-align: center;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .dashboard-header::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
                        pointer-events: none;
                    }
                    
                    .dashboard-header h1 {
                        font-weight: 700;
                        font-size: 3rem;
                        margin: 0;
                        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                        position: relative;
                        z-index: 1;
                    }
                    
                    .content-section {
                        padding: 2rem;
                    }
                    
                    .total-spending-card {
                        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                        color: white;
                        border-radius: 15px;
                        padding: 2rem;
                        text-align: center;
                        margin: 2rem 0;
                        box-shadow: 0 10px 30px rgba(72, 187, 120, 0.3);
                        transform: translateY(-10px);
                    }
                    
                    .total-spending-card h1 {
                        font-size: 2.5rem;
                        font-weight: 600;
                        margin: 0;
                        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
                    }
                    
                    .section-card {
                        background: white;
                        border-radius: 15px;
                        padding: 1rem;
                        margin: 1rem 0;
                        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
                        border: 1px solid rgba(0, 0, 0, 0.05);
                    }
                    
                    .section-title {
                        color: #2d3748;
                        font-weight: 600;
                        font-size: 1.75rem;
                        margin-bottom: 1.5rem;
                        text-align: center;
                        position: relative;
                    }
                    
                    .section-title::after {
                        content: '';
                        position: absolute;
                        bottom: -8px;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 60px;
                        height: 3px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 2px;
                    }
                    
                    .dropdown-container {
                        background: white;
                        border-radius: 15px;
                        padding: 1.5rem;
                        z-index: 10;
                    }
                    
                    .Select-control {
                        border: 2px solid #e2e8f0 !important;
                        border-radius: 10px !important;
                        box-shadow: none !important;
                        font-weight: 500;
                    }
                    
                    .Select-control:hover {
                        border-color: #667eea !important;
                    }
                    
                    .color-legend {
                        background: white;
                        border-radius: 15px;
                        padding: 2rem;
                        margin: 2rem 0;
                        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
                        border: 1px solid rgba(0, 0, 0, 0.05);
                    }
                    
                    .color-box {
                        border-radius: 4px !important;
                        border: 2px solid rgba(0, 0, 0, 0.1) !important;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    }
                    
                    .logout-btn {
                        position: absolute;
                        top: 1rem;
                        right: 2rem;
                        background: rgba(255, 255, 255, 0.15) !important;
                        border: 2px solid rgba(255, 255, 255, 0.3) !important;
                        color: white !important;
                        font-weight: 500;
                        padding: 0.5rem 1.5rem;
                        border-radius: 25px;
                        text-decoration: none !important;
                        transition: all 0.2s ease;
                        backdrop-filter: blur(10px);
                        z-index: 10;
                    }
                    
                    .logout-btn:hover {
                        background: rgba(255, 255, 255, 0.25) !important;
                        border-color: rgba(255, 255, 255, 0.5) !important;
                        transform: translateY(-1px);
                    }
                    
                    .plotly-graph-div {
                        border-radius: 10px;
                        overflow: hidden;
                    }
                    
                    @keyframes slideIn {
                        from {
                            opacity: 0;
                            transform: translateY(20px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }
                    
                    .section-card {
                        animation: slideIn 0.6s ease-out;
                    }
                    
                    /* Dropdown animations */
                    #dropdowns-content {
                        max-height: 500px;
                        transition: max-height 0.3s ease-out;
                    }
                    
                    #dropdowns-content.minimized,
                    #transactions-minimize-section.minimized {
                        max-height: 0;
                        overflow: hidden;
                    }

                    #dropdowns-content,
                    #transactions-minimize-section {
                        max-height: 2000px;
                        transition: max-height 0.3s ease-out;
                    }

                    .last-updated {
                        font-family: 'Inter', sans-serif;
                        font-weight: 400;
                    }
                    
                    /* Mobile responsiveness */
                    @media (max-width: 768px) {
                        .main-container {
                            margin: 10px;
                            min-height: calc(100vh - 20px);
                        }
                        
                        .dashboard-header {
                            padding: 1.5rem;
                        }
                        
                        .dashboard-header h1 {
                            font-size: 2rem;
                        }
                        
                        .content-section {
                            padding: 1rem;
                        }
                        
                        .logout-btn {
                            position: static;
                            display: block;
                            width: fit-content;
                            margin: 1rem auto 0;
                        }

                        .last-updated {
                            position: static !important;
                            display: block;
                            text-align: center;
                            margin-bottom: 1rem;
                        }
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        """

        # Set layout and register callbacks
        self.app.layout = self._create_layout
        self._register_callbacks()

    def get_and_set_data_if_new(self):
        current_modified = fetch_csv_last_modified()
        if current_modified > self.last_modified:
            print("Refreshing data!")
            self.df = fetch_transaction_df_all()
            self.purchases_df = self.df[self.df.amount > 0]

            # Get month data
            month_periods = self.df["Month"].sort_values().unique()
            self.month_names = [
                self.df[self.df["Month"] == m]["Month_Name"].iloc[0]
                for m in month_periods
            ]
            self.max_month = self.month_names[-1]
            self.last_modified = current_modified
            last_updated_dt = pd.to_datetime(current_modified, unit="s")
            self.last_updated = last_updated_dt.strftime("%b %-d, %Y")
        else:
            print("Data is up-to-date.")

    def _create_layout(self):
        """Create the enhanced dashboard layout"""
        # Refresh data every load
        self.get_and_set_data_if_new()

        return html.Div(
            [
                html.Div(
                    [
                        # Header section
                        html.Div(
                            [
                                html.Span(
                                    f"Last updated: {self.last_updated}",
                                    className="last-updated",
                                    style={
                                        "position": "absolute",
                                        "left": "2rem",
                                        "top": "1rem",
                                        "color": "white",
                                        "fontSize": "0.9rem",
                                        "opacity": "0.8",
                                        "zIndex": "1",
                                    },
                                ),
                                html.A(
                                    "Logout",
                                    href="/logout",
                                    className="logout-btn",
                                ),
                                html.H1(
                                    "Financial Dashboard",
                                    style={"position": "relative", "zIndex": 1},
                                ),
                            ],
                            className="dashboard-header",
                        ),
                        # Content section
                        html.Div(
                            [
                                # Selectors with minimize button
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.H3(
                                                            "Filters",
                                                            style={
                                                                "margin": "0",
                                                                "display": "inline-block",
                                                                "color": "#4a5568",
                                                                "fontWeight": "600",
                                                            },
                                                        ),
                                                        html.Button(
                                                            "+",
                                                            id="minimize-button",
                                                            style={
                                                                "float": "right",
                                                                "border": "none",
                                                                "background": "none",
                                                                "fontSize": "24px",
                                                                "color": "#4a5568",
                                                                "cursor": "pointer",
                                                                "padding": "0 10px",
                                                            },
                                                        ),
                                                    ],
                                                    style={
                                                        "marginBottom": "1rem",
                                                        "padding": "0.5rem 0",
                                                    },
                                                    id="filters-header",
                                                    n_clicks=1,
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.Label(
                                                                    "Select Time Period",
                                                                    style={
                                                                        "fontWeight": "600",
                                                                        "marginBottom": "1rem",
                                                                        "textAlign": "center",
                                                                        "color": "#4a5568",
                                                                    },
                                                                ),
                                                                dcc.Dropdown(
                                                                    options=[
                                                                        {
                                                                            "label": name,
                                                                            "value": name,
                                                                        }
                                                                        for name in self.month_names
                                                                    ]
                                                                    + [
                                                                        {
                                                                            "label": "Last 30 Days",
                                                                            "value": "Last 30 Days",
                                                                        }
                                                                    ],
                                                                    value=self.max_month,
                                                                    id="timespan-selection",
                                                                ),
                                                            ],
                                                            className="dropdown-container",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Label(
                                                                    "Select Spender",
                                                                    style={
                                                                        "fontWeight": "600",
                                                                        "marginBottom": "1rem",
                                                                        "textAlign": "center",
                                                                        "color": "#4a5568",
                                                                    },
                                                                ),
                                                                dcc.Dropdown(
                                                                    options=[
                                                                        {
                                                                            "label": name,
                                                                            "value": name,
                                                                        }
                                                                        for name in [
                                                                            "Both",
                                                                            "Jay",
                                                                            "Cara",
                                                                        ]
                                                                    ]
                                                                    + [
                                                                        {
                                                                            "label": "Both",
                                                                            "value": "Both",
                                                                        }
                                                                    ],
                                                                    value="Both",
                                                                    id="source-selection",
                                                                ),
                                                            ],
                                                            className="dropdown-container",
                                                        ),
                                                    ],
                                                    id="dropdowns-content",
                                                    className="minimized",
                                                ),
                                            ],
                                        ),
                                    ],
                                    className="section-card",
                                ),
                                # Budget progress section
                                html.Div(
                                    [
                                        html.H2("Envelopes", className="section-title"),
                                        html.Div(id="budget-progress-section"),
                                    ],
                                    className="section-card",
                                ),
                                # Treemap section
                                html.Div(
                                    [
                                        html.H2(
                                            "Spending Breakdown",
                                            className="section-title",
                                        ),
                                        dcc.Graph(id="treemap-content"),
                                    ],
                                    className="section-card",
                                ),
                                # Recent Transactions section
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Recent Transactions",
                                                    style={
                                                        "margin": "0",
                                                        "display": "inline-block",
                                                        "color": "#4a5568",
                                                        "fontWeight": "600",
                                                    },
                                                ),
                                                html.Button(
                                                    "+",
                                                    id="transactions-minimize-button",
                                                    style={
                                                        "float": "right",
                                                        "border": "none",
                                                        "background": "none",
                                                        "fontSize": "24px",
                                                        "color": "#4a5568",
                                                        "cursor": "pointer",
                                                        "padding": "0 10px",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "marginBottom": "1rem",
                                                "padding": "0.5rem 0",
                                            },
                                            id="transactions-header",
                                            n_clicks=1,
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    id="transactions-table",
                                                ),
                                                html.Div(
                                                    [
                                                        dbc.Pagination(
                                                            max_value=10,  # how to set dynamically?
                                                            fully_expanded=False,
                                                            style={
                                                                "textAlign": "center",
                                                                "marginTop": "1rem",
                                                                "fontSize": "14px",
                                                            },
                                                            id="transactions-pagination",
                                                        )
                                                    ],
                                                    style={"marginTop": "1rem"},
                                                ),
                                            ],
                                            id="transactions-minimize-section",
                                            className="minimized",
                                        ),
                                    ],
                                    className="section-card",
                                ),
                            ],
                            className="content-section",
                        ),
                    ],
                    className="main-container",
                )
            ]
        )

    def _filter_data_by_selectors(self, timespan_value, source_selection):
        """Filter purchase data based on selected timespan"""
        if timespan_value == "Last 30 Days":
            time_filter = self.purchases_df["date"] >= (
                pd.Timestamp.now() - pd.DateOffset(days=30)
            )
        else:
            time_filter = self.purchases_df.Month_Name == timespan_value
        dff = self.purchases_df[time_filter]
        # If not both (looking at individual) filter out non-extra/essential categories
        if source_selection != "Both":
            source_filter = dff["account_id"].str.contains(source_selection) & ~dff[
                "personal_finance_category.primary"
            ].isin(NON_EXTRA_CATEGORIES)
        else:
            source_filter = np.array([True] * len(dff))
        dff = dff[source_filter]
        # Default to sorted so we don't have to recompute
        self.dff = dff.sort_values(by="date", ascending=False)

    def _register_callbacks(self):
        """Register all dashboard callbacks"""

        @callback(
            [
                Output("treemap-content", "figure"),
                Output("budget-progress-section", "children"),
                Output("transactions-table", "children"),
                Output("transactions-pagination", "active_page"),
                Output("transactions-pagination", "max_value"),
            ],
            [Input("timespan-selection", "value"), Input("source-selection", "value")],
        )
        def update_whole_dashboard_on_filter_change(timespan_value, source_selection):
            self._filter_data_by_selectors(timespan_value, source_selection)
            if len(self.dff) == 0:
                return {}, html.Div("No data available for the selected filters.")
            treemap = update_treemap()
            budget_section = update_budget_progress(source_selection)
            transactions_table = update_transactions_table(1)
            max_pages = len(self.dff) // TRANSACTIONS_TABLE_PAGE_SIZE + 1
            return treemap, budget_section, transactions_table, 1, max_pages

        def update_treemap():
            chart = px.treemap(
                self.dff,
                path=["personal_finance_category.primary", "merchant_name"],
                values="amount",
                color="personal_finance_category.primary",
                color_discrete_map=self.category_colors,
                hover_data=["name", "amount", "date", "account_id"],
            )

            # Enhanced chart styling
            chart.update_traces(
                marker=dict(cornerradius=8, line=dict(width=2, color="white")),
                textfont_size=16,
                textfont_color="black",
                textfont_family="Inter",
            )

            chart.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=14, color="#4a5568"),
            )

            return chart

        def update_budget_progress(source_selection):
            if source_selection == "Both":
                return create_budget_section(self.dff, self.category_budgets)
            else:
                return create_budget_section(self.dff, self.individual_budgets)

        @callback(
            Output("transactions-table", "children", allow_duplicate=True),
            Input("transactions-pagination", "active_page"),
            prevent_initial_call=True,
        )
        def update_transactions_table(page):
            start_idx = (page - 1) * TRANSACTIONS_TABLE_PAGE_SIZE
            end_idx = start_idx + TRANSACTIONS_TABLE_PAGE_SIZE
            rows = self.dff.iloc[start_idx:end_idx]
            transactions_table = html.Div(
                html.Table(
                    [
                        # Header
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th(
                                        col,
                                        style={
                                            "textAlign": "left",
                                            "padding": "12px",
                                            "borderBottom": "2px solid #e2e8f0",
                                            "color": "#4a5568",
                                            "fontWeight": "600",
                                        },
                                    )
                                    for col in [
                                        "Date",
                                        "Merchant",
                                        "Amount",
                                        "Category",
                                        "Account",
                                    ]
                                ]
                            )
                        ),
                        # Body
                        html.Tbody(
                            [
                                html.Tr(
                                    [
                                        html.Td(
                                            row["date"].strftime("%Y-%m-%d"),
                                            style={
                                                "padding": "12px",
                                                "borderBottom": "1px solid #e2e8f0",
                                            },
                                        ),
                                        html.Td(
                                            row["merchant_name"],
                                            style={
                                                "padding": "12px",
                                                "borderBottom": "1px solid #e2e8f0",
                                            },
                                        ),
                                        html.Td(
                                            f"${row['amount']:.2f}",
                                            style={
                                                "padding": "12px",
                                                "borderBottom": "1px solid #e2e8f0",
                                                "textAlign": "right",
                                            },
                                        ),
                                        html.Td(
                                            row["personal_finance_category.primary"],
                                            style={
                                                "padding": "12px",
                                                "borderBottom": "1px solid #e2e8f0",
                                            },
                                        ),
                                        html.Td(
                                            row["account_id"],
                                            style={
                                                "padding": "12px",
                                                "borderBottom": "1px solid #e2e8f0",
                                            },
                                        ),
                                    ],
                                    style={"backgroundColor": "white"},
                                )
                                for _, row in rows.iterrows()  # Show only the 10 most recent transactions
                            ]
                        ),
                    ],
                    style={
                        "width": "100%",
                        "borderCollapse": "collapse",
                        "backgroundColor": "white",
                        "boxShadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1)",
                    },
                ),
                style={
                    "borderRadius": "10px",
                    "overflow": "auto",
                    "boxShadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1)",
                    "backgroundColor": "white",
                },
            )
            return transactions_table

        @callback(
            [
                Output("dropdowns-content", "className"),
                Output("minimize-button", "children"),
            ],
            Input("filters-header", "n_clicks"),
            prevent_initial_call=True,
        )
        def toggle_dropdown_visibility(n_clicks):
            if n_clicks % 2 == 1:
                return "minimized", "+"
            return "", "−"  # Unicode minus sign

        @callback(
            [
                Output("transactions-minimize-section", "className"),
                Output("transactions-minimize-button", "children"),
            ],
            Input("transactions-header", "n_clicks"),
            prevent_initial_call=True,
        )
        def toggle_transactions_visibility(n_clicks):
            return toggle_dropdown_visibility(n_clicks)


def create_dashboard(server):
    """Factory function to create and return dashboard instance"""
    dashboard = FinanceDashboard(server)
    return dashboard.app
