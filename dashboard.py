from dash import (
    Dash,
    html,
    dcc,
    callback,
    Output,
    Input,
    State,
    ALL,
    callback_context,
)
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from overrides_helpers import upsert_override, delete_override
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
import os


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
        template_path = os.path.join(
            os.path.dirname(__file__), "templates", "index.html"
        )
        with open(template_path, "r") as f:
            self.app.index_string = f.read()

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

        # Get all unique categories for the dropdown
        all_categories = list(self.category_colors.keys())

        return html.Div(
            [
                html.Div(id="dummy-output"),  # Hidden div for the edit callback
                # Edit Transaction Modal
                dbc.Modal(
                    [
                        dbc.ModalHeader("Edit Transaction"),
                        dbc.ModalBody(
                            [
                                dbc.Form(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Label("Amount", width=2),
                                                dbc.Col(
                                                    dbc.Input(
                                                        type="number",
                                                        step=0.01,
                                                        id="edit-amount-input",
                                                        style={"width": "100%"},
                                                    ),
                                                    width=10,
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Label("Category", width=2),
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id="edit-category-dropdown",
                                                        options=[
                                                            {"label": cat, "value": cat}
                                                            for cat in all_categories
                                                        ],
                                                        style={"width": "100%"},
                                                    ),
                                                    width=10,
                                                ),
                                            ]
                                        ),
                                        # Hidden input to store transaction_id
                                        dbc.Input(
                                            id="edit-transaction-id", type="hidden"
                                        ),
                                    ]
                                )
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Reset to Original",
                                    id="edit-modal-reset",
                                    className="me-auto",
                                    color="danger",
                                ),
                                dbc.Button(
                                    "Cancel",
                                    id="edit-modal-close",
                                    className="me-2",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Save", id="edit-modal-save", color="primary"
                                ),
                            ]
                        ),
                    ],
                    id="edit-modal",
                    size="lg",
                ),
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
                ),
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
            [
                Input("timespan-selection", "value"),
                Input("source-selection", "value"),
                Input("dummy-output", "children"),
            ],
        )
        def update_whole_dashboard_on_filter_change(
            timespan_value, source_selection, dummy_val
        ):
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
                                        "Actions",
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
                                        html.Td(
                                            html.Button(
                                                "Edit",
                                                id={
                                                    "type": "edit-transaction",
                                                    "index": row["transaction_id"],
                                                },
                                                style={
                                                    "backgroundColor": "#4299e1",
                                                    "color": "white",
                                                    "border": "none",
                                                    "padding": "8px 16px",
                                                    "borderRadius": "4px",
                                                    "cursor": "pointer",
                                                },
                                            ),
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

        @callback(
            [
                Output("edit-modal", "is_open"),
                Output("edit-transaction-id", "value"),
                Output("edit-amount-input", "value"),
                Output("edit-category-dropdown", "value"),
            ],
            [
                Input({"type": "edit-transaction", "index": ALL}, "n_clicks"),
                Input("edit-modal-close", "n_clicks"),
                Input("edit-modal-save", "n_clicks"),
                Input("edit-modal-reset", "n_clicks"),
            ],
            [
                State({"type": "edit-transaction", "index": ALL}, "id"),
                State("edit-modal", "is_open"),
            ],
        )
        def toggle_edit_modal(
            edit_clicks, close_clicks, save_clicks, reset_clicks, button_ids, is_open
        ):
            ctx = callback_context
            if not ctx.triggered:
                raise PreventUpdate

            trigger_id = ctx.triggered[0]["prop_id"]

            # Handle modal close/save/reset buttons
            if (
                "edit-modal-close" in trigger_id
                or "edit-modal-save" in trigger_id
                or "edit-modal-reset" in trigger_id
            ):
                return False, "", None, None

            # Handle initial load case - all edit_clicks will be None
            if all(click is None for click in edit_clicks):
                raise PreventUpdate

            # Handle edit button clicks
            if ".n_clicks" in trigger_id:
                button_index = eval(trigger_id.split(".")[0])["index"]
                transaction_id = button_index

                # Get current transaction data
                row = self.dff[self.dff["transaction_id"] == transaction_id].iloc[0]
                current_amount = row["amount"]
                current_category = row["personal_finance_category.primary"]

                return True, transaction_id, current_amount, current_category

            raise PreventUpdate

        @callback(
            Output("dummy-output", "children"),
            [
                Input("edit-modal-save", "n_clicks"),
                Input("edit-modal-reset", "n_clicks"),
            ],
            [
                State("edit-transaction-id", "value"),
                State("edit-amount-input", "value"),
                State("edit-category-dropdown", "value"),
            ],
        )
        def handle_edit_save_or_reset(
            save_n_clicks, reset_n_clicks, transaction_id, new_amount, new_category
        ):
            if not save_n_clicks and not reset_n_clicks:
                raise PreventUpdate

            if not transaction_id:
                raise PreventUpdate

            ctx = callback_context
            if not ctx.triggered:
                raise PreventUpdate

            trigger_id = ctx.triggered[0]["prop_id"]
            print(trigger_id)
            if "edit-modal-reset" in trigger_id:
                delete_override(transaction_id)
                self.get_and_set_data_if_new()  # Refresh data after edit
                return ""

            if "edit-modal-save" in trigger_id and (
                new_amount is not None or new_category is not None
            ):
                upsert_override(
                    transaction_id=transaction_id,
                    new_amount=float(new_amount) if new_amount else None,
                    new_category=new_category,
                )
                self.get_and_set_data_if_new()  # Refresh data after edit
                return ""

            raise PreventUpdate


def create_dashboard(server):
    """Factory function to create and return dashboard instance"""
    dashboard = FinanceDashboard(server)
    return dashboard.app
