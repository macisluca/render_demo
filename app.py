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
from layouts.forecasting import (
    get_forecasting_global_layout,
    get_forecasting_country_layout
    )
from utils.data_loader import (
    load_all_data,
    load_crisis_data,
    load_electoral_data,
    load_event_data,
    load_ACLED_event_data,
    load_WDI_data
)

import os

# Paths to the relevant folders
FORECAST_PATH = 'models/TiDE/predictions/'
FORECAST_HTML_PATH = 'docs/figures/operative/TiDE/'
ISO3_PATH = 'data/raw/ACLED_coverage_ISO3.csv'


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

# Load WDI data
wdi_data = load_WDI_data()

frequencies = ["daily", "weekly", "monthly"]

# You would prepare and pass the necessary arguments for forecasting
available_variables = ["battles fatalities", "violence index"]  # example list
crisis_weeks = list(sorted(crisis_data['end of the week'].unique()))

default_variable = available_variables[0]
crisis_weeks = crisis_weeks[0]

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
        return get_monitoring_acled_layout(frequencies)
    elif pathname == '/monitoring/worldbank':
        return get_monitoring_worldbank_layout(wdi_data)
    elif pathname == '/monitoring/elections':
        return get_monitoring_elections_layout(elections_df)
    elif pathname == '/forecasting/global':
        return get_forecasting_global_layout(available_variables, default_variable)
    elif pathname == '/forecasting/country':
        return get_forecasting_country_layout(available_variables, default_variable)
    
    else:
        # Default page
        return get_monitoring_acled_layout(frequencies)


# Import callbacks so they register with the app
import callbacks.monitoring_callbacks as mc
import callbacks.worldbank_callbacks as wc
import callbacks.forecasting_callbacks as fc
import callbacks.elections_callbacks as ec

if __name__ == '__main__':
    app.run_server(debug=True)
