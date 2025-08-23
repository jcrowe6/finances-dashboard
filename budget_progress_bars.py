from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def create_budget_progress_bar(
    category, spent_amount, budget_amount, color, icon_url=None
):
    """
    Create a horizontal progress bar showing budget usage

    Args:
        category: Category name
        spent_amount: Amount spent in the category
        budget_amount: Budget limit for the category
        color: Color for the progress bar

    Returns:
        Dash component with the progress bar
    """
    percentage = (
        min((spent_amount / budget_amount) * 100, 100) if budget_amount > 0 else 0
    )
    is_over_budget = spent_amount > budget_amount

    # Create the plotly figure for the progress bar
    fig = go.Figure()

    # Add the background bar (full budget)
    fig.add_trace(
        go.Bar(
            x=[budget_amount],
            y=[category],
            orientation="h",
            marker=dict(color="lightgray", opacity=0.3),
            showlegend=False,
            hoverinfo="skip",
            width=0.6,
        )
    )

    # Add the progress bar (spent amount)
    progress_color = "red" if is_over_budget else color
    fig.add_trace(
        go.Bar(
            x=[spent_amount],
            y=[category],
            orientation="h",
            marker=dict(color=progress_color, opacity=0.8),
            showlegend=False,
            hovertemplate=f"<b>{category}</b><br>"
            + f"Spent: ${spent_amount:,.2f}<br>"
            + f"Budget: ${budget_amount:,.2f}<br>"
            + f"Remaining: ${budget_amount - spent_amount:,.2f}<br>"
            + "<extra></extra>",
            width=0.6,
        )
    )

    # Update layout for clean appearance
    fig.update_layout(
        height=80,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            range=[0, max(budget_amount * 1.1, spent_amount * 1.1)],
        ),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        barmode="overlay",
    )

    # Format the text display
    status_text = "Over Budget!" if is_over_budget else f"{percentage:.1f}% used"
    status_color = (
        "danger" if is_over_budget else "success" if percentage < 80 else "warning"
    )

    category_to_name = {
        "GENERAL_MERCHANDISE": "Groceries",
        "FOOD_AND_DRINK": "Restaurants",
        "TRANSPORTATION": "Gas",
        "Total": "Total",
    }

    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            src=icon_url,
                                            style={
                                                "width": "24px",
                                                "height": "24px",
                                                "marginRight": "8px",
                                                "verticalAlign": "middle",
                                            },
                                        )
                                        if icon_url
                                        else None,
                                        html.H5(
                                            category_to_name[category], className="mb-1"
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.B(
                                    f"${spent_amount:,.2f} / ${budget_amount:,.2f}",
                                    className="text-muted",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Badge(
                                    status_text,
                                    color=status_color,
                                    className="float-end",
                                )
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-2",
                ),
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "60px"},
                ),
            ],
            className="p-3",
        ),
        className="mb-3 shadow-sm",
    )


def create_budget_section(purchases_df, budgets):
    """
    Create a section with budget progress bars for specified categories

    Args:
        purchases_df: DataFrame with purchase data
        month_name: Selected month name
        budgets: Dictionary with category budgets

    Returns:
        Dash component with all budget progress bars
    """

    # Define colors for each category (matching your existing color scheme)
    category_colors = {
        "GENERAL_MERCHANDISE": "lightblue",
        "FOOD_AND_DRINK": "orange",
        "TRANSPORTATION": "lightcoral",
    }

    progress_bars = []

    for category in [
        "Total",
        "GENERAL_MERCHANDISE",
        "FOOD_AND_DRINK",
        "TRANSPORTATION",
    ]:
        # Calculate spent amount for this category
        if category == "Total":
            category_data = purchases_df
        else:
            category_data = purchases_df[
                purchases_df["personal_finance_category.primary"] == category
            ]
        spent_amount = category_data["amount"].sum() if not category_data.empty else 0

        budget_amount = budgets.get(category, 0)

        # Get color
        color = category_colors.get(category, "lightblue")

        icon_url = None
        if (
            not category_data.empty
            and "personal_finance_category_icon_url" in category_data.columns
        ):
            icon_url = category_data["personal_finance_category_icon_url"].iloc[0]

        # Create progress bar
        progress_bar = create_budget_progress_bar(
            category, spent_amount, budget_amount, color, icon_url
        )
        progress_bars.append(progress_bar)

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("Envelopes", className="text-center mb-4"),
                            *progress_bars,
                        ]
                    )
                ]
            )
        ],
        className="mb-5",
    )
