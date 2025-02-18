from app_instance import app, server
import dash
from dash import dcc, html
from layouts import navbar
from layouts.monitoring import (
    get_monitoring_eddy_layout,
    get_monitoring_acled_layout,
    get_monitoring_worldbank_layout,
    get_monitoring_elections_layout
)
from layouts.forecasting import get_forecasting_layout
from utils.data_loader import (
    load_all_data,
    load_crisis_data,
    load_electoral_data,
    load_event_data,
    load_ACLED_event_data
)

import os

# Paths to the relevant folders
DATA_PATH = 'data/interim/data_ready/'
FORECAST_PATH = 'models/TiDE/predictions/'
FORECAST_HTML_PATH = 'docs/figures/operative/TiDE/'
ISO3_PATH = 'data/raw/ACLED_coverage_ISO3.csv'

# Load initial data
data = load_all_data()
# Extract available dates and other options
available_dates = sorted(data['event_date'].unique())[:-36]
default_date = available_dates[-1]

available_variables = sorted([f for f in os.listdir(FORECAST_PATH) if os.path.isdir(os.path.join(FORECAST_PATH, f))], reverse=True)
default_variable = available_variables[1]

available_windows = ["12", "24", "36"]
default_window = available_windows[0]

# Load electoral data
elections_df = load_electoral_data()

# Load initial crisis data
crisis_data = load_crisis_data(default_variable, default_window)
crisis_weeks = list(sorted(crisis_data['end of the week'].unique()))

# Event Raw Data
event_data = load_event_data()
available_event_dates = sorted(event_data['event_date'].unique())
default_event_date = available_event_dates[-1]

# Column dropdown options
unavailable_cols = ['event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon', 'month', 'quarter', 'week', 'violence index_exp_moving_avg', 'General', 'Legislative', 'Local', 'Parliamentary', 'Presidential', 'Referendum', 'holiday']
unavailable_table_cols = ['country', 'month', 'quarter', 'week', 'event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon', 'violence index_exp_moving_avg', 'General', 'Legislative', 'Local', 'Parliamentary', 'Presidential', 'Referendum', 'holiday']
column_options = [{'label': col, 'value': col} for col in data.columns if col not in unavailable_cols]

# Crisis type dropdown options
crisis_type_options = [
    {'label': 'Probability of Extreme Crisis (%)', 'value': 'probability of extreme crisis (%)'},
    {'label': 'Probability of Severe Crisis (%)', 'value': 'probability of severe crisis (%)'},
    {'label': 'Probability of Mild Crisis (%)', 'value': 'probability of mild crisis (%)'}
]

# ACLED event Raw Data
acled_event_data = load_ACLED_event_data()
available_acled_event_dates = sorted(acled_event_data['event_date'].unique())
default_acled_event_date = available_acled_event_dates[-1]

# Build a dictionary to pass into layout functions if needed
layout_args = {
    'available_event_dates': available_acled_event_dates,
    'default_event_date': default_acled_event_date,
    'available_dates': available_dates,
    'default_date': default_date,
    'data': data,
    'crisis_weeks': crisis_weeks,
    'column_options': column_options
}

# Main layout with page routing
app.layout = html.Div([
    dcc.Location(id="url"),
    navbar.navbar,
    html.Div(id="page-content")  # This is your container
])

# A simple page routing callback
@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/monitoring/eddy':
        return get_monitoring_eddy_layout(available_event_dates, default_event_date)
    elif pathname == '/monitoring/acled':
        return get_monitoring_acled_layout(**layout_args)
    elif pathname == '/monitoring/worldbank':
        return get_monitoring_worldbank_layout()
    elif pathname == '/monitoring/elections':
        return get_monitoring_elections_layout(elections_df)
    elif pathname == '/forecasting':
        # You would prepare and pass the necessary arguments for forecasting
        available_variables = ["battles fatalities", "violence index"]  # example list
        available_windows = ["12", "24", "36"]
        crisis_weeks = list(sorted(crisis_data['end of the week'].unique()))

        default_variable = available_variables[0]
        default_window = available_windows[0]
        crisis_weeks = crisis_weeks[0]
        return get_forecasting_layout(available_variables, default_variable, available_windows, default_window, crisis_weeks)
    else:
        # Default page
        return get_monitoring_eddy_layout(available_event_dates, default_event_date)


# Import callbacks so they register with the app
import callbacks.monitoring_callbacks as mc
import callbacks.worldbank_callbacks as wc
import callbacks.forecasting_callbacks as fc
import callbacks.elections_callbacks as ec

print("🔍 Registered callbacks:", app.callback_map.keys())  # DEBUG

if __name__ == '__main__':
    app.run_server(debug=True)
