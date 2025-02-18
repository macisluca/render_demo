from dash import dcc, html
import dash_bootstrap_components as dbc
from utils.date_utils import transform_date_to_day_first
from utils.data_loader import load_all_data

data = load_all_data()

# Crisis type dropdown options
crisis_type_options = [
    {'label': 'Probability of Extreme Crisis (%)', 'value': 'probability of extreme crisis (%)'},
    {'label': 'Probability of Severe Crisis (%)', 'value': 'probability of severe crisis (%)'},
    {'label': 'Probability of Mild Crisis (%)', 'value': 'probability of mild crisis (%)'}
]

def get_forecasting_layout(available_variables, default_variable, available_windows, default_window, crisis_weeks):
    layout = html.Div([
    html.H1('Forecasting Dashboard'),
    html.H2('Global Forecasting'),
    html.H3('Select variable to forecast:'),
    dcc.Dropdown(id='forecast-variable', options=[{'label': variable, 'value': variable} for variable in available_variables], value=default_variable, clearable=False, className='dcc-dropdown'),
    html.H3('Select forecasting window:'),
    dcc.Dropdown(id='forecast-window', options=[{'label': window, 'value': window} for window in available_windows], value=default_window, clearable=False, className='dcc-dropdown'),
    html.H3('Select forecasted week:'),
    dcc.Slider(id='forecast-slider', min=0, max=11, step=1, value=0, marks={}),
    html.H3('Select outcome level: (0 = min outcome predicted, 100 = max outcome predicted)'),
    dcc.Slider(id='percentile-slider', min=0, max=100, step=1, value=50, marks={i: str(i) for i in range(0, 101, 10)}),
    dcc.Graph(id='forecast-bar-plot', className='dcc-graph'),
    html.H3('Select number of countries:'),
    dcc.Slider(id='num-forecasted-countries', min=10, max=160, step=10, value=10, marks={i: str(i) for i in range(10, 160, 10)}),
    dcc.Graph(id='forecast-world-map', className='dcc-graph'),
    html.H2('Select Country Forecasts'),
    dcc.Dropdown(id='forecast-country', options=[{'label': c, 'value': c} for c in sorted(data['country'].unique())], value='Afghanistan', clearable=False, className='dcc-dropdown'),
    html.Iframe(id='forecast-line-plot', style={'width': '100%', 'height': '600px'}),
    html.H2('Crisis Map'),
    html.H3('The Crisis Map illustrates the likelihood of each country approaching its historical peak of violence, based on past trends and predictive analysis.'),
    dcc.Dropdown(id='crisis-end-week', options=[{'label': transform_date_to_day_first(week), 'value': week} for week in crisis_weeks], value=crisis_weeks[0], clearable=False, className='dcc-dropdown'),
    dcc.Dropdown(id='crisis-type', options=crisis_type_options, value='probability of mild crisis (%)', clearable=False, className='dcc-dropdown'),
    dcc.Graph(id='crisis-world-map', className='dcc-graph'),
    html.Footer(
        [
        "Modifications from ACLED Data: Violence index calculated based on the paper ",
        html.A("Violence Index: a new data-driven proposal to conflict monitoring", href="https://dx.doi.org/10.4995/CARMA2024.2024.17831", target="_blank"),
        ],
    style={'textAlign': 'center', 'fontSize': 'small', 'padding': '10px'}
    ),
])
    return layout

