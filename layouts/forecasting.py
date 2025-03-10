import os
import pandas as pd
from dash import dcc, html
from utils.date_utils import transform_date_to_day_first

def get_country_list(variable, window):
    # Build the directory path
    directory = os.path.join("models/TiDE/predictions", variable, window)
    # List all files that end with '.csv'
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    # Remove the file extension to get the country names
    country_names = [os.path.splitext(f)[0] for f in csv_files]
    country_names.sort()
    return country_names

def get_forecasting_global_layout(available_variables, default_variable):
    # Define available windows and a default
    available_windows = ["daily", "weekly", "monthly"]
    default_window = "weekly"
    default_country = 'AFG'
    
    # Build the CSV path for default selections:
    csv_path = os.path.join("models/TiDE/predictions", default_variable, default_window, f"{default_country}.csv")
    try:
        df = pd.read_csv(csv_path)
        forecasted_dates = sorted(df['forecast'].unique())
    except Exception as e:
        forecasted_dates = []
    
    default_forecasted_date = forecasted_dates[0] if forecasted_dates else None
    
    layout = html.Div([
        html.H1('Forecasting Dashboard'),
        html.Div(className='container', children=[
            html.H2('Global Forecasting'),
            html.H3('Select variable to forecast:'),
            dcc.Dropdown(
                id='forecast-variable',
                options=[{'label': var, 'value': var} for var in available_variables],
                value=default_variable,
                clearable=False,
                className='dcc-dropdown'
            ),
            html.H3('Select daily/weekly/monthly forecasts:'),
            dcc.Dropdown(
                id='forecast-window',
                options=[{'label': win, 'value': win} for win in available_windows],
                value=default_window,
                clearable=False,
                className='dcc-dropdown'
            ),
            html.H3('Select forecasted date:'),
            dcc.Dropdown(
                id='forecast-date',
                options=[{'label': date, 'value': date} for date in forecasted_dates],
                value=default_forecasted_date,
                clearable=False,
                className='dcc-dropdown'
            ),
            # NEW: Explanation text container for simplified categories.
            html.Div(
                id='simplified-category-explanation',
                style={'fontSize': 'small', 'color': 'grey', 'marginTop': '10px'},
                children="Explanation will appear here."
            ),
            html.H3('Forecast World Map (Simplified):'),
            dcc.Graph(id='forecast-world-map-simplified', className='dcc-graph'),
            html.H3('Select Simplified Category:'),
            # The options will be updated via a callback.
            dcc.Dropdown(
                id='simplified-category',
                options=[],  
                value=None,
                clearable=False,
                className='dcc-dropdown'
            ),
            html.H3('Select number of countries to display in bar plot:'),
            dcc.Slider(
                id='num-countries-bar-forecast',
                min=10,
                max=190,
                step=10,
                value=10,
                marks={i: str(i) for i in range(10, 191, 10)}
            ),
            html.H3('Forecast Bar Plot (Simplified):'),
            dcc.Graph(id='forecast-bar-plot-simplified', className='dcc-graph'),
            html.Footer(
                [
                    "Modifications from ACLED Data: Violence index calculated based on the paper ",
                    html.A(
                        "Violence Index: a new data-driven proposal to conflict monitoring",
                        href="https://dx.doi.org/10.4995/CARMA2024.2024.17831", target="_blank"
                    ),
                ],
                style={'textAlign': 'center', 'fontSize': 'small', 'padding': '10px'}
            ),
        ]),
    ])
    return layout


def get_forecasting_country_layout(available_variables, default_variable):
    # Define available windows and a default
    available_windows = ["daily", "weekly", "monthly"]
    default_window = "weekly"
    default_country = 'AFG'
    countries = get_country_list(default_variable, default_window)
    
    # Build the CSV path for default selections:
    csv_path = os.path.join("models/TiDE/predictions", default_variable, default_window, f"{default_country}.csv")
    print(csv_path)
    try:
        df = pd.read_csv(csv_path)
        forecasted_dates = sorted(df['forecast'].unique())
    except Exception as e:
        forecasted_dates = []
    
    # Set a default forecast date if available
    if forecasted_dates:
        default_forecasted_date = forecasted_dates[0]
    else:
        default_forecasted_date = None
    
    layout = html.Div([
        html.H1('Forecasting Dashboard'),
        html.Div(className='container', children=[
        html.H2('Countries Forecasts'),
        html.H3('Select variable to forecast:'),
        dcc.Dropdown(
            id='forecast-variable-country',
            options=[{'label': var, 'value': var} for var in available_variables],
            value=default_variable,
            clearable=False,
            className='dcc-dropdown'
        ),
        html.H3('Select daily/weekly/monthly forecasts:'),
        dcc.Dropdown(
            id='forecast-window-country',
            options=[{'label': win, 'value': win} for win in available_windows],
            value=default_window,
            clearable=False,
            className='dcc-dropdown'
        ),
        html.H3('Select country to forecast:'),
        dcc.Dropdown(
            id='forecast-country',
            options=[{'label': c, 'value': c} for c in countries],
            value=default_country,
            clearable=False,
            className='dcc-dropdown'
        ),
        html.H3('Select forecasted date:'),
        dcc.Dropdown(
            id='forecast-date-country',
            options=[{'label': date, 'value': date} for date in forecasted_dates],
            value=default_forecasted_date,
            clearable=False,
            className='dcc-dropdown'
        ),
        html.H3('Select display mode:'),
        dcc.RadioItems(
            id="forecast-display-mode",
            options=[
                {"label": "Detailed", "value": "detailed"},
                {"label": "Simplified", "value": "simplified"}
            ],
            value="detailed",
            labelStyle={"display": "inline-block", "margin-right": "20px"}
        ),
        html.Div([
                html.P("Detailed View: this mode displays the full distribution of forecast outcomes. If there are many unique values, the data will be binned so that you can see a more granular distribution, allowing you to analyze variations across the entire range."),
                html.P("Simplified View: this mode aggregates the forecast outcomes into four predefined categories (for example, Mild/Moderate/Intense/Critical for violence index or No/Low/Medium/High Fatalities for battles fatalities) and shows cumulative percentages. It provides a concise summary of the forecast distribution.")],
                style={'fontSize': 'small', 'color': 'lightgrey', 'marginTop': '10px'}),
        dcc.Graph(id='forecast-bar-plot', className='dcc-graph'),
        html.Footer(
            [
                "Modifications from ACLED Data: Violence index calculated based on the paper ",
                html.A(
                    "Violence Index: a new data-driven proposal to conflict monitoring",
                    href="https://dx.doi.org/10.4995/CARMA2024.2024.17831", target="_blank"
                ),
            ],
            style={'textAlign': 'center', 'fontSize': 'small', 'padding': '10px'}
        ),
        ]),
    ])
    return layout


