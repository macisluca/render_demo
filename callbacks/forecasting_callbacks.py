import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from app_instance import app

from utils.date_utils import get_majority_category
from utils.data_loader import load_ISO3_data, load_all_data



def load_forecast_data_wrapper(selected_variable, selected_window, selected_country):
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
    Generates a detailed bar plot for the filtered forecast data.
    
    - If the number of unique outcome values exceeds 100, the outcomes are binned into 100 bins.
      The bins are computed using 101 equally spaced endpoints (which are then rounded to integers),
      so the bin intervals are based on these rounded endpoints.
    - In the non-binned (detailed) case:
      • For 'violence index', bars are colored by levels (Mild, Moderate, Intense, Critical).
      • For 'battles fatalities', bars are colored by category based on thresholds:
            0 → "No Fatalities" (white),
            0 < outcome ≤ 10 → "Low Fatalities" (light coral),
            10 < outcome ≤ 50 → "Medium Fatalities" (red),
            outcome > 50 → "High Fatalities" (dark red).
      • For other variables, a default color (blue) is used.
    """
    unique_count = len(df_filtered['outcome'].unique())
    
    if unique_count > 100 and selected_variable.lower().strip() != "violence index":
        # Binning: use 100 endpoints for 100 bins.
        min_val = df_filtered['outcome'].min()
        max_val = df_filtered['outcome'].max()
        # Compute 101 equally spaced endpoints and round them to nearest integer.
        bins = np.linspace(min_val, max_val, num=101)
        bins = np.round(bins).astype(int)
        bins = np.unique(bins)  # In case rounding causes duplicates.
        
        df_binned = df_filtered.copy()
        df_binned['binned'] = pd.cut(df_binned['outcome'], bins=bins, right=False, include_lowest=True)
        binned_counts = df_binned['binned'].value_counts().sort_index()
        total = df_filtered.shape[0]
        percentages = (binned_counts / total) * 100
        x_values = [str(interval) for interval in binned_counts.index]
        plot_df = pd.DataFrame({
            'bin': x_values,
            'percentage': percentages.values
        })
        
        # For battles fatalities in binned mode, assign category based on the interval’s left bound.
        if selected_variable.lower().strip() == "battles fatalities":
            def get_battle_category(interval):
                lower = interval.left
                if lower == 0:
                    return "No Fatalities"
                elif lower <= 10:
                    return "Low Fatalities"
                elif lower <= 50:
                    return "Medium Fatalities"
                else:
                    return "High Fatalities"
            bin_categories = [get_battle_category(interval) for interval in binned_counts.index]
            plot_df['category'] = bin_categories
            color_map = {
                "No Fatalities": "white",
                "Low Fatalities": "lightcoral",
                "Medium Fatalities": "red",
                "High Fatalities": "darkred"
            }
            fig = px.bar(
                plot_df,
                x='bin',
                y='percentage',
                color='category',
                color_discrete_map=color_map,
                template='plotly_dark',
                title=f"Forecast Probability Distribution for {selected_forecast_date}"
            )
        else:
            fig = px.bar(
                plot_df,
                x='bin',
                y='percentage',
                template='plotly_dark',
                title=f"Forecast Probability Distribution for {selected_forecast_date}"
            )
        fig.update_layout(xaxis_title="Outcome Range", yaxis_title="Probability (%)")
        return fig

    else:
        # Non-binned detailed plot: use individual outcome values.
        max_outcome = int(df_filtered['outcome'].max())
        x_values = list(range(0, max_outcome + 1))
        # Round outcomes for counting.
        counts = [(np.round(df_filtered['outcome']) == x).sum() for x in x_values]
        total = df_filtered.shape[0]
        percentages = [(count / total) * 100 for count in counts]
        plot_df = pd.DataFrame({
            'outcome': x_values,
            'percentage': percentages
        })
        
        if selected_variable.lower().strip() == "violence index":
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
                title=f"Forecast Probability Distribution for {selected_forecast_date}"
            )
        elif selected_variable.lower().strip() == "battles fatalities":
            def get_battle_category(val):
                if val == 0:
                    return "No Fatalities"
                elif val <= 10:
                    return "Low Fatalities"
                elif val <= 50:
                    return "Medium Fatalities"
                else:
                    return "High Fatalities"
            plot_df['category'] = plot_df['outcome'].apply(get_battle_category)
            color_map = {
                "No Fatalities": "white",
                "Low Fatalities": "lightcoral",
                "Medium Fatalities": "red",
                "High Fatalities": "darkred"
            }
            fig = px.bar(
                plot_df,
                x='outcome',
                y='percentage',
                color='category',
                color_discrete_map=color_map,
                template='plotly_dark',
                title=f"Forecast Probability Distribution for {selected_forecast_date}"
            )
        else:
            fig = px.bar(
                plot_df,
                x='outcome',
                y='percentage',
                template='plotly_dark',
                title=f"Forecast Probability Distribution for {selected_forecast_date}"
            )
            fig.update_traces(marker_color='blue')
        fig.update_layout(xaxis_title="Outcome Value", yaxis_title="Probability (%)")
        return fig


def generate_simplified_plot(df_filtered, selected_forecast_date, selected_variable):
    """
    Generates a simplified bar plot for the forecast variable.
    For 'violence index', groups outcomes into four levels (Mild, Moderate, Intense, Critical).
    For 'battles fatalities', groups outcomes into four categories:
         - No Fatalities (outcome == 0)
         - Low Fatalities (0 < outcome <= 10)
         - Medium Fatalities (10 < outcome <= 50)
         - High Fatalities (outcome > 50)
    For other variables, falls back to the detailed plot.
    """
    if selected_variable.lower().strip() == "battles fatalities":
        def get_battle_category(val):
            if val == 0:
                return "No Fatalities"
            elif val <= 10:
                return "Low Fatalities"
            elif val <= 50:
                return "Medium Fatalities"
            else:
                return "High Fatalities"
        df_simpl = df_filtered.copy()
        df_simpl["category"] = df_simpl["outcome"].apply(get_battle_category)
        category_counts = df_simpl.groupby("category")["outcome"].count()
        total = df_simpl.shape[0]
        category_percentages = category_counts / total * 100
        simple_df = category_percentages.reset_index()
        # Ensure the categories appear in order.
        order = ["No Fatalities", "Low Fatalities", "Medium Fatalities", "High Fatalities"]
        simple_df["category"] = pd.Categorical(simple_df["category"], categories=order, ordered=True)
        simple_df = simple_df.sort_values("category")
        color_map = {
            "No Fatalities": "white",
            "Low Fatalities": "lightcoral",
            "Medium Fatalities": "red",
            "High Fatalities": "darkred"
        }
        fig = px.bar(
            simple_df,
            x="category",
            y="outcome",  # 'outcome' now holds the count (we can rename it)
            color="category",
            color_discrete_map=color_map,
            template="plotly_dark",
            title=f"Forecast Cumulative Probability Distribution for {selected_forecast_date}"
        )
        # Convert counts to percentages:
        fig.update_layout(
            xaxis_title="Battles Fatalities Category",
            yaxis_title="Probability (%)"
        )
        # Alternatively, compute percentages beforehand:
        simple_df["percentage"] = simple_df["outcome"]
        fig = px.bar(
            simple_df,
            x="category",
            y="percentage",
            color="category",
            color_discrete_map=color_map,
            template="plotly_dark",
            title=f"Forecast Cumulative Probability Distribution for {selected_forecast_date}"
        )
        fig.update_layout(
            xaxis_title="Battles Fatalities Category",
            yaxis_title="Probability (%)"
        )
        return fig
    elif selected_variable.lower().strip() == "violence index":
        def get_level(val):
            if val < 25:
                return "Mild"
            elif val < 50:
                return "Moderate"
            elif val < 75:
                return "Intense"
            else:
                return "Critical"
        df_simpl = df_filtered.copy()
        df_simpl["level"] = df_simpl["outcome"].apply(get_level)
        level_counts = df_simpl.groupby("level")["outcome"].count()
        total = df_simpl.shape[0]
        level_percentages = level_counts / total * 100
        simple_df = level_percentages.reset_index()
        order = ["Mild", "Moderate", "Intense", "Critical"]
        simple_df["level"] = pd.Categorical(simple_df["level"], categories=order, ordered=True)
        simple_df = simple_df.sort_values("level")
        fig = px.bar(
            simple_df,
            x="level",
            y="outcome",  # using the count as percentage, if precomputed
            color="level",
            color_discrete_map={
                "Mild": "green",
                "Moderate": "yellow",
                "Intense": "orange",
                "Critical": "red"
            },
            template="plotly_dark",
            title=f"Forecast Cumulative Probability Distribution for {selected_forecast_date}"
        )
        # If needed, update layout titles:
        fig.update_layout(
            xaxis_title="Violence Index Level",
            yaxis_title="Probability (%)"
        )
        return fig
    else:
        return generate_detailed_plot(df_filtered, selected_variable, selected_forecast_date)


@app.callback(
    [Output('forecast-date', 'options'),
     Output('forecast-date', 'value')],
    [Input('forecast-variable', 'value'),
     Input('forecast-window', 'value'),
     Input('forecast-date', 'value')]
)
def update_forecasting_global_dashboard(selected_variable, selected_window, selected_forecast_date):
    # Load the CSV data using the wrapper function.
    df = load_forecast_data_wrapper(selected_variable, selected_window, 'AFG')
    if df is None:
        return [], None, {}
    forecasted_dates, forecast_date_options = get_forecast_date_options(df)

    if selected_forecast_date not in forecasted_dates:
        selected_forecast_date = forecasted_dates[0] if forecasted_dates else None  
    return forecast_date_options, selected_forecast_date


@app.callback(
    [Output('forecast-date-country', 'options'),
     Output('forecast-date-country', 'value'),
     Output('forecast-bar-plot-det', 'figure'),
     Output('forecast-bar-plot-sim', 'figure')],
    [Input('forecast-variable-country', 'value'),
     Input('forecast-window-country', 'value'),
     Input('forecast-countries', 'value'),
     Input('forecast-country-distribution', 'value'),
     Input('forecast-date-country', 'value')]
)
def update_forecasting_dashboard(selected_variable, selected_window, selected_countries, selected_country, selected_forecast_date):
    # Load the CSV data using the wrapper function.
    df = load_forecast_data_wrapper(selected_variable, selected_window, selected_country)
    if df is None:
        return [], None, {}
    forecasted_dates, forecast_date_options = get_forecast_date_options(df)
    if selected_forecast_date not in forecasted_dates:
        selected_forecast_date = forecasted_dates[0] if forecasted_dates else None
    df_filtered = df[df['forecast'] == selected_forecast_date]
    if not df_filtered.empty:
        fig_det = generate_detailed_plot(df_filtered, selected_variable, selected_forecast_date)
        fig_sim = generate_simplified_plot(df_filtered, selected_forecast_date, selected_variable)
    return forecast_date_options, selected_forecast_date, fig_det, fig_sim


@app.callback(
    Output('forecast-world-map-simplified', 'figure'),
    [Input('forecast-variable', 'value'),
     Input('forecast-window', 'value'),
     Input('forecast-date', 'value')]
)
def update_forecast_world_map_simplified(selected_variable, selected_window, selected_forecast_date):
    # Define the base path for CSV files
    csv_path = os.path.join("models/TiDE/predictions", selected_variable, selected_window)
    
    # Get all country CSV filenames (assuming files are named by country)
    try:
        countries_folder = [f[:-4] for f in os.listdir(csv_path) if f.endswith('.csv')]
    except FileNotFoundError:
        print(f"Directory not found: {csv_path}")
        return {}

    results = []

    for country_name in countries_folder:
        country_csv_path = os.path.join(csv_path, f"{country_name}.csv")
        
        try:
            df_country = pd.read_csv(country_csv_path)
        except Exception as e:
            print(f"Error reading {country_csv_path}: {e}")
            continue  # Skip this country if there's an issue
        
        # Filter data for the selected forecast date
        df_country = df_country[df_country["forecast"] == selected_forecast_date]
        if df_country.empty:
            continue

        # Compute the majority (simplified) category
        majority_category = get_majority_category(df_country, selected_variable)
        if majority_category is not None:
            results.append({
                "ISO_3": country_name,  # Assuming the filename is the ISO3 code
                "category": majority_category
            })

    if not results:
        return {}

    results_df = pd.DataFrame(results)

    # Define color mapping based on the selected variable
    variable_lower = selected_variable.lower().strip()
    color_maps = {
        "violence index": {
            "Mild": "green",
            "Moderate": "yellow",
            "Intense": "orange",
            "Critical": "red"
        },
        "battles fatalities": {
            "No Fatalities": "white",
            "Low Fatalities": "lightcoral",
            "Medium Fatalities": "red",
            "High Fatalities": "darkred"
        }
    }

    color_map = color_maps.get(variable_lower, {})

    # Create the choropleth map using Plotly
    fig = px.choropleth(
        results_df,
        locations="ISO_3",
        color="category",
        hover_name="category",
        projection="natural earth",
        color_discrete_map=color_map if color_map else None,
        template="plotly_dark",
        title=f"Forecast Simplified Majority Category for {selected_forecast_date}"
    )

    return fig


@app.callback(
    [Output('simplified-category', 'options'),
     Output('simplified-category', 'value')],
    [Input('forecast-variable', 'value')]
)
def update_simplified_category_options(selected_variable):
    if selected_variable is None:
        return [], None
    var = selected_variable.lower().strip()
    if var == "violence index":
        options = [
            {"label": "Mild", "value": "Mild"},
            {"label": "Moderate", "value": "Moderate"},
            {"label": "Intense", "value": "Intense"},
            {"label": "Critical", "value": "Critical"}
        ]
        default_value = "Critical"
    elif var == "battles fatalities":
        options = [
            {"label": "No Fatalities", "value": "No Fatalities"},
            {"label": "Low Fatalities", "value": "Low Fatalities"},
            {"label": "Medium Fatalities", "value": "Medium Fatalities"},
            {"label": "High Fatalities", "value": "High Fatalities"}
        ]
        default_value = "High Fatalities"
    else:
        # For other variables, we might not have a simplified category.
        options = []
        default_value = None
    return options, default_value


def compute_category_probability(df, selected_variable, chosen_category):
    """
    Computes the percentage of rows in df whose outcome falls into the chosen simplified category.
    """
    var = selected_variable.lower().strip()
    if var == "violence index":
        def get_level(val):
            if val < 25:
                return "Mild"
            elif val < 50:
                return "Moderate"
            elif val < 75:
                return "Intense"
            else:
                return "Critical"
        df = df.copy()
        df["level"] = df["outcome"].apply(get_level)
        prob = (df["level"] == chosen_category).mean() * 100
        return prob
    elif var == "battles fatalities":
        def get_battle_category(val):
            if val == 0:
                return "No Fatalities"
            elif val <= 10:
                return "Low Fatalities"
            elif val <= 50:
                return "Medium Fatalities"
            else:
                return "High Fatalities"
        df = df.copy()
        df["category"] = df["outcome"].apply(get_battle_category)
        prob = (df["category"] == chosen_category).mean() * 100
        return prob
    else:
        return None



@app.callback(
    Output('forecast-bar-plot-simplified', 'figure'),
    [Input('forecast-variable', 'value'),
     Input('forecast-window', 'value'),
     Input('forecast-date', 'value'),
     Input('simplified-category', 'value'),
     Input('num-countries-bar-forecast', 'value')]
)
def update_forecast_bar_plot_simplified(selected_variable, selected_window, selected_forecast_date, chosen_category, num_countries):

    # Define the base path for CSV files
    csv_path = os.path.join("models/TiDE/predictions", selected_variable, selected_window)
    
    # Get all country CSV filenames (assuming files are named by country)
    try:
        countries_folder = [f[:-4] for f in os.listdir(csv_path) if f.endswith('.csv')]
    except FileNotFoundError:
        print(f"Directory not found: {csv_path}")
        return {}

    results = []

    for country_name in countries_folder:
        country_csv_path = os.path.join(csv_path, f"{country_name}.csv")
        
        try:
            df_country = pd.read_csv(country_csv_path)
        except Exception as e:
            print(f"Error reading {country_csv_path}: {e}")
            continue  # Skip this country if there's an issue
        
        # Filter data for the selected forecast date
        df_country = df_country[df_country["forecast"] == selected_forecast_date]
        if df_country.empty:
            continue
        # Compute the probability by category
        prob = compute_category_probability(df_country, selected_variable, chosen_category)
        if prob is not None:
            results.append({"Country": country_name, "ISO_3": country_name, "Probability": prob})

    if not results:
        return {}

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="Probability", ascending=False).head(num_countries)
    fig = px.bar(
        results_df,
        x="Country",
        y="Probability",
        color="Probability",
        color_continuous_scale='orrd',
        template="plotly_dark",
        title=f"Probability of {chosen_category} on {selected_forecast_date}"
    )
    fig.update_layout(xaxis_title="Country", yaxis_title="Probability (%)")
    return fig

@app.callback(
    Output('simplified-category-explanation', 'children'),
    [Input('forecast-variable', 'value')]
)
def update_category_explanation(selected_variable):
    if selected_variable is None:
        return ""
    var = selected_variable.lower().strip()
    if var == "violence index":
        return (
            "For Violence Index: "
            "Mild (<25), Moderate (25-50), Intense (50-75), Critical (>75)."
        )
    elif var == "battles fatalities":
        return (
            "For Battles Fatalities: "
            "No Fatalities (=0), Low Fatalities (>0 and <=10), "
            "Medium Fatalities (>10 and <=50), High Fatalities (>50)."
        )
    else:
        return "No simplified categories available for this variable."


def load_forecast_data_wrapper(selected_variable, selected_window, selected_country):
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

def get_bounds(samples_array_list: list, lower_bound_percent=5, upper_bound_percent=95):
    """
    Calculate the lower, mid, and upper bounds for a list of sample arrays based on given percentiles.
    """
    lower_bound_list = [np.percentile(samples_array, lower_bound_percent) for samples_array in samples_array_list]
    upper_bound_list = [np.percentile(samples_array, upper_bound_percent) for samples_array in samples_array_list]
    mid_bound_list = [np.percentile(samples_array, 50) for samples_array in samples_array_list]

    return mid_bound_list, lower_bound_list, upper_bound_list

def hex_to_rgba(hex_color, opacity):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{opacity})'

@app.callback(
    [Output('forecast-line-plot', 'figure')],
    [Input('forecast-countries', 'value'),
     Input('forecast-window-country', 'value'),
     Input('forecast-variable-country', 'value')]
)
def line_plot_country_predictions(selected_countries, selected_window, target_name):
    """
    Plot countries prediction image.
    
    Returns:
        Figure: A line plot figure with historical and forecast data.
    """
    # Define a discrete color mapping for selected countries
    color_sequence = px.colors.qualitative.Plotly
    color_mapping = {country: color_sequence[i % len(color_sequence)] 
                     for i, country in enumerate(selected_countries)}
    
    # Load historical data (assumed to include 'event_date' and target_name)
    data = load_all_data(selected_window)
    
    # Create the plot
    fig = go.Figure()
    
    for country in selected_countries:
        # Use each country's own data rather than concatenating all together
        country_data = data[data['ISO_3'] == country]
        # Use only the last 12 events
        dates_plot = country_data['event_date'].tail(12).to_list()
        # Convert dates to datetime for proper x-axis handling
        dates_plot = [pd.to_datetime(d) for d in dates_plot]
        
        if target_name == 'battles fatalities':
            target_name_bf = 'Fatalities_Battles'
            target_values = country_data[target_name_bf].to_list()
        else:
            target_values = country_data[target_name].to_list()
        if not target_values:
            continue  # Skip if no historical data
        
        max_value = max(target_values)
        target_values = target_values[-12:]
        
        # Load predictions for the current country
        samples_array_list = []
        df = load_forecast_data_wrapper(target_name, selected_window, country)
        if df is None:
            continue
        forecasted_dates, _ = get_forecast_date_options(df)
        for date in forecasted_dates:
            date_df = df[df['forecast'] == date]
            samples_array = np.array(date_df['outcome'].to_list())
            samples_array_list.append(samples_array)
        
        # Combine the last 12 historical dates with forecasted dates and convert to datetime
        forecast_dates = [pd.to_datetime(d) for d in forecasted_dates]
        full_dates = dates_plot + forecast_dates
        
        # Calculate bounds (using lists directly, since they are scalars)
        mid_bounds, lower_bounds, upper_bounds = get_bounds(samples_array_list, 1, 99)
        # For additional CIs:
        _, lower25_bounds, upper75_bounds = get_bounds(samples_array_list, 25, 75)
        _, lower40_bounds, upper60_bounds = get_bounds(samples_array_list, 40, 60)
        
        # Create x-axis values for forecasts: starting from the last historical date index
        shifted_x = list(range(len(target_values) - 1, len(target_values) + len(mid_bounds)))
    
        # Add past values trace
        fig.add_trace(go.Scatter(
            x=list(range(len(target_values))),
            y=target_values,
            mode='lines',
            name=f'{country} Past',
            line=dict(color=color_mapping[country])
        ))
        
        # Add forecast values trace (starting from the last historical value)
        fig.add_trace(go.Scatter(
            x=shifted_x,
            y=[target_values[-1]] + list(mid_bounds),
            mode='lines+markers',
            name=f'{country} Forecast',
            line=dict(color=color_mapping[country]),
            showlegend=True
        ))
        
        # Add confidence interval traces
        fig.add_trace(go.Scatter(
            x=shifted_x + shifted_x[::-1], 
            y=[target_values[-1]] + list(lower_bounds) + ([target_values[-1]] + list(upper_bounds))[::-1],
            fill='toself', 
            fillcolor=hex_to_rgba(color_mapping[country], 0.25),
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{country} 1-99% CI',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=shifted_x + shifted_x[::-1], 
            y=[target_values[-1]] + list(lower25_bounds) + ([target_values[-1]] + list(upper75_bounds))[::-1],
            fill='toself',
            fillcolor=hex_to_rgba(color_mapping[country], 0.35),
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{country} 25-75% CI',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=shifted_x + shifted_x[::-1], 
            y=[target_values[-1]] + list(lower40_bounds) + ([target_values[-1]] + list(upper60_bounds))[::-1],
            fill='toself',
            fillcolor=hex_to_rgba(color_mapping[country], 0.45),
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{country} 40-60% CI',
            showlegend=False
        ))
        """
        # Add a horizontal line for the max historical value
        fig.add_trace(go.Scatter(
            x=[0, len(target_values) + len(mid_bounds) - 1],
            y=[max_value, max_value],
            mode='lines',
            name=f'{country} Max Historical: {round(max_value, 0)}',
            line=dict(color=color_mapping[country], dash='dash'),
            showlegend=True
        ))
        """

    
    full_dates = dates_plot + forecast_dates
    # Configure the layout; using full_dates for tick labels if desired
    fig.update_layout(
        title='Countries Predictions',
        template='plotly_dark',
        xaxis_title='Date',
        yaxis_title=target_name,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(full_dates))),
            ticktext=[d.strftime('%Y-%m-%d') for d in full_dates]
        ),
        yaxis=dict(range=[0, None]),
        margin=dict(b=160),
        legend=dict(orientation='h', y=-0.3),
        showlegend=True
    )

    return [fig]


