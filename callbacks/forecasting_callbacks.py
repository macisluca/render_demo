import os
import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output
from app_instance import app
from utils.data_loader import load_forecast_data, load_crisis_data, load_ISO3_data
from utils.date_utils import transform_date_to_day_first


def load_forecast_data(selected_variable, selected_window, selected_country):
    """
    Loads forecast CSV data from the specified path.
    Returns the DataFrame or None if the file cannot be read.
    """
    csv_path = os.path.join("models/TiDE/predictions", selected_variable, selected_window, f"{selected_country}.csv")
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"Error loading CSV at {csv_path}: {e}")
        return None


def get_forecast_date_options(df):
    """
    Given a DataFrame with a 'forecast' column,
    returns a sorted list of unique forecast dates as options.
    """
    forecasted_dates = sorted(df['forecast'].unique())
    options = [{'label': date, 'value': date} for date in forecasted_dates]
    return forecasted_dates, options


def generate_detailed_plot(df_filtered, selected_variable, selected_forecast_date):
    """
    Generates the detailed bar plot for the filtered forecast data.
    If the variable is 'violence index', it applies conditional coloring.
    """
    max_outcome = int(df_filtered['outcome'].max())
    x_values = list(range(0, max_outcome + 1))
    counts = [(np.round(df_filtered['outcome']) == x).sum() for x in x_values]
    total = df_filtered.shape[0]
    percentages = [(count / total) * 100 for count in counts]
    
    plot_df = pd.DataFrame({
        'outcome': x_values,
        'percentage': percentages
    })

    if selected_variable.lower() == "violence index":
        # Map outcome value to level synonym
        def get_level(val):
            if val < 25:
                return "Mild"
            elif val < 50:
                return "Moderate"
            elif val < 75:
                return "Intense"
            else:
                return "Critical"
        plot_df['level'] = plot_df['outcome'].apply(get_level)
        fig = px.bar(
            plot_df,
            x='outcome',
            y='percentage',
            color='level',
            color_discrete_map={
                "Mild": "green",
                "Moderate": "yellow",
                "Intense": "orange",
                "Critical": "red"
            },
            template='plotly_dark',
            title=f"Forecast Percent Distribution for {selected_forecast_date}"
        )
    else:
        fig = px.bar(
            plot_df,
            x='outcome',
            y='percentage',
            template='plotly_dark',
            title=f"Forecast Percent Distribution for {selected_forecast_date}"
        )
        fig.update_traces(marker_color='blue')

    fig.update_layout(
        xaxis_title="Outcome Value",
        yaxis_title="Percentage (%)"
    )
    return fig


def generate_simplified_plot(df_filtered, selected_forecast_date):
    """
    Generates a simplified bar plot for the 'violence index' variable by grouping
    outcome values into 4 levels and computing cumulative percentages.
    """
    # Define the levels for violence index
    def get_level(val):
        if val < 25:
            return "Mild"
        elif val < 50:
            return "Moderate"
        elif val < 75:
            return "Intense"
        else:
            return "Critical"
    
    df_filtered = df_filtered.copy()
    df_filtered["level"] = df_filtered["outcome"].apply(get_level)
    level_counts = df_filtered.groupby("level")["outcome"].count()
    total = df_filtered.shape[0]
    level_percentages = level_counts / total * 100
    simple_df = level_percentages.reset_index().rename(columns={"outcome": "percentage"})
    
    # Ensure the levels are in a specific order:
    order = ["Mild", "Moderate", "Intense", "Critical"]
    simple_df["level"] = pd.Categorical(simple_df["level"], categories=order, ordered=True)
    simple_df = simple_df.sort_values("level")
    
    fig = px.bar(
        simple_df,
        x="level",
        y="percentage",
        color="level",
        color_discrete_map={
            "Mild": "green",
            "Moderate": "yellow",
            "Intense": "orange",
            "Critical": "red"
        },
        template="plotly_dark",
        title=f"Forecast Cumulative Percent Distribution for {selected_forecast_date}"
    )
    fig.update_layout(
        xaxis_title="Violence Index Level",
        yaxis_title="Percentage (%)"
    )
    return fig


@app.callback(
    [Output('forecast-date', 'options'),
     Output('forecast-date', 'value'),
     Output('forecast-bar-plot', 'figure')],
    [Input('forecast-variable', 'value'),
     Input('forecast-window', 'value'),
     Input('forecast-country', 'value'),
     Input('forecast-date', 'value'),
     Input('forecast-display-mode', 'value')]
)
def update_forecasting_dashboard(selected_variable, selected_window, selected_country, selected_forecast_date, display_mode):
    # Load the CSV data
    df = load_forecast_data(selected_variable, selected_window, selected_country)
    if df is None:
        return [], None, {}

    # Get forecast date options from the CSV
    forecasted_dates, forecast_date_options = get_forecast_date_options(df)
    if selected_forecast_date not in forecasted_dates:
        selected_forecast_date = forecasted_dates[0] if forecasted_dates else None

    # Filter the DataFrame for the selected forecast date
    df_filtered = df[df['forecast'] == selected_forecast_date]

    # Generate the appropriate plot based on display mode
    if df_filtered.empty:
        fig = {}
    else:
        if display_mode == "detailed":
            fig = generate_detailed_plot(df_filtered, selected_variable, selected_forecast_date)
        else:  # simplified mode
            if selected_variable.lower() == "violence index":
                fig = generate_simplified_plot(df_filtered, selected_forecast_date)
            else:
                # For non-violence index, fallback to detailed view
                fig = generate_detailed_plot(df_filtered, selected_variable, selected_forecast_date)

    return forecast_date_options, selected_forecast_date, fig
