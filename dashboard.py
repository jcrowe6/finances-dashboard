from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from datafetchers import fetch_transaction_df_all, fetch_csv_last_modified
from budget_progress_bars import create_budget_section


class FinanceDashboard:
    def __init__(self, server, category_budgets, category_colors):
        self.server = server
        self.category_budgets = category_budgets
        self.category_colors = category_colors

        # Load and process data
        self.last_modified = 0
        self.get_and_set_data_if_new()

        # Initialize Dash app
        self.app = Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            url_base_pathname="/",
        )

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
        else:
            print("Data is up-to-date.")

    def _create_layout(self):
        """Create the dashboard layout"""
        # Refresh data every load
        self.get_and_set_data_if_new()
        return dbc.Container(
            [
                # Header with logout button
                dbc.Row(
                    dbc.Col(
                        [
                            html.A(
                                "Logout",
                                href="/logout",
                                className="btn btn-outline-danger btn-sm",
                            )
                        ],
                        width=12,
                        className="text-end py-2",
                    )
                ),
                # Main title
                dbc.Row(
                    dbc.Col(html.H1("Finances", className="text-center my-4"), width=12)
                ),
                # Time period selector
                dbc.Row(
                    dbc.Col(
                        dcc.Dropdown(
                            options=[
                                {"label": name, "value": name}
                                for name in self.month_names
                            ]
                            + [{"label": "Last 30 Days", "value": "Last 30 Days"}],
                            value="Last 30 Days",
                            id="timespan-selection",
                            className="mb-4",
                        ),
                        width={"size": 6, "offset": 3},
                    )
                ),
                # Total spending display
                dbc.Row(
                    dbc.Col(
                        html.H1(
                            id="total-spending-value", className="text-center mb-4"
                        ),
                        width=12,
                    )
                ),
                # Budget progress section
                dbc.Row(dbc.Col(html.Div(id="budget-progress-section"), width=12)),
                # Treemap section
                dbc.Row(
                    dbc.Col(
                        html.H2("Spending Treemap", className="text-center mb-4"),
                        width=12,
                    )
                ),
                dbc.Row(dbc.Col(dcc.Graph(id="treemap-content"), width=12)),
                # Color legend
                self._create_color_legend(),
            ],
            fluid=True,
            className="px-4",
        )

    def _create_color_legend(self):
        """Create the color legend for categories"""
        return dbc.Row(
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
                                    for category, color in self.category_colors.items()
                                ],
                                className="text-center",
                            )
                        ],
                        className="mt-3",
                    )
                ]
            )
        )

    def _filter_data_by_timespan(self, timespan_value):
        """Filter purchase data based on selected timespan"""
        if timespan_value == "Last 30 Days":
            return self.purchases_df[
                self.purchases_df["date"]
                >= (pd.Timestamp.now() - pd.DateOffset(days=30))
            ]
        else:
            return self.purchases_df[self.purchases_df.Month_Name == timespan_value]

    def _register_callbacks(self):
        """Register all dashboard callbacks"""

        @callback(
            Output("treemap-content", "figure"), Input("timespan-selection", "value")
        )
        def update_treemap(timespan_value):
            dff = self._filter_data_by_timespan(timespan_value)

            chart = px.treemap(
                dff,
                path=["personal_finance_category.primary", "merchant_name"],
                values="amount",
                color="personal_finance_category.primary",
                color_discrete_map=self.category_colors,
                hover_data=["name", "amount", "date"],
            )
            chart.update_traces(marker=dict(cornerradius=5), textfont_size=20)
            chart.update_layout(margin=dict(l=10, r=10, t=20, b=10))

            return chart

        @callback(
            Output("total-spending-value", "children"),
            Input("timespan-selection", "value"),
        )
        def update_total_spending(timespan_value):
            dff = self._filter_data_by_timespan(timespan_value)
            total = dff["amount"].sum()
            return f"Total Spending: ${total:,.2f}"

        @callback(
            Output("budget-progress-section", "children"),
            Input("timespan-selection", "value"),
        )
        def update_budget_progress(timespan_value):
            dff = self._filter_data_by_timespan(timespan_value)
            return create_budget_section(dff, self.category_budgets)


def create_dashboard(server, category_budgets, category_colors):
    """Factory function to create and return dashboard instance"""
    dashboard = FinanceDashboard(server, category_budgets, category_colors)
    return dashboard.app
