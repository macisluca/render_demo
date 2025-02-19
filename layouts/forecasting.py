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

def get_forecasting_layout(available_variables, default_variable):
    # Define available windows and a default
    available_windows = ["daily", "weekly", "monthly"]
    default_window = "weekly"
    default_country = 'Afghanistan'
    countries = get_country_list(default_variable, default_window)
    
    # Build the CSV path for default selections:
    csv_path = os.path.join("models/TiDE/predictions", default_variable, default_window, f"{default_country}.csv")
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
            id='forecast-date',
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
    ])
    return layout


