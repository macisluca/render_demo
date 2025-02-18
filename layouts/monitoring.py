from dash import dcc, html, dash_table
from utils.date_utils import transform_date_to_day_first
from utils.data_loader import load_WDI_data


def get_monitoring_eddy_layout(available_event_dates, default_event_date):
    layout = html.Div([
        html.H1('Monitoring Events'),
        html.Div(className='container', children=[
            html.H2('Global Daily Events Map'),
            html.H3('Select a date, and the map will display the events that occurred on that day.'),
            dcc.Dropdown(id='map-date', options=[{'label': date, 'value': date} for date in available_event_dates], value=default_event_date, clearable=False, className='dcc-dropdown'),
            dcc.Graph(id='event-map', className='dcc-graph')
        ]),
    ])
    return layout

# Assume that data like `available_event_dates`, `default_event_date`, etc. have been loaded in app.py
def get_monitoring_acled_layout(available_event_dates, default_event_date, available_dates, default_date, data, crisis_weeks, column_options):
    layout = html.Div([
    html.H1('Monitoring ACLED Events'),
    html.Div(className='container', children=[
        html.H2('Global Daily Events Map'),
        html.H3('Select a date, and the map will display the events that occurred on that day.'),
        dcc.Dropdown(id='acled-map-date', options=[{'label': date, 'value': date} for date in available_event_dates], value=default_event_date, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='acled-event-map', className='dcc-graph'),
        html.H2('Ranking by Variable on a weekly basis'),
        dcc.Dropdown(id='ranking-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
        dcc.Dropdown(id='ranking-date', options=[{'label': transform_date_to_day_first(date), 'value': date} for date in available_dates], value=default_date, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='bar-plot', className='dcc-graph'),
        html.H3('Select number of countries:'),
        dcc.Slider(id='num-countries', min=10, max=235, step=10, value=10, marks={i: str(i) for i in range(10, 236, 10)}),
        dcc.Graph(id='world-map', className='dcc-graph'),
        html.H2('Countries Weekly Stats Over Time'),
        dcc.Dropdown(id='evolution-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
        dcc.Dropdown(id='evolution-country', options=[{'label': c, 'value': c} for c in sorted(data['country'].unique())], value=['Afghanistan'], multi=True, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='line-plot', className='dcc-graph'),
        dcc.Dropdown(id='plot-date', options=[{'label': transform_date_to_day_first(date), 'value': date} for date in available_dates], value=default_date, clearable=False, className='dcc-dropdown'),
        dash_table.DataTable(id='data-table',
            style_data={'color': 'white','backgroundColor': 'rgb(50, 50, 50)'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'height': 'auto', 'minWidth': '90px', 'width': '180px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
            # Add conditional styling for rows with "violence index"
            style_data_conditional=[
                {'if': {'filter_query': '{Country} contains "index"'},
                 'color':'rgb(255, 200, 200)','backgroundColor': 'rgb(60, 50, 50)'}
                 ]
        ),
        ]),
    ])
    return layout


wdi_df = load_WDI_data()

def get_monitoring_worldbank_layout():
    """
    Returns the layout for the Monitoring World Bank Data Dashboard.
    
    :param wdi_df: A pandas DataFrame containing the World Bank data.
                   Expected to have columns like 'Country', 'ISO_3', 'year', etc.
    """
    # Exclude non-numeric or identifier columns for ranking selection
    excluded_cols = ['ISO_3', 'ISO_3166-3', 'Country', 'year']
    dropdown_options = [{'label': col, 'value': col} 
                        for col in wdi_df.columns if col not in excluded_cols]

    layout = html.Div([
        html.H1('Monitoring World Bank Data Dashboard'),
        html.Div(className='container', children=[
            html.H2('Ranking by Variable on an Annual Basis'),
            dcc.Dropdown(
                id='wb-ranking-column',
                options=dropdown_options,
                # Default to the third column if available
                value=dropdown_options[2]['value'] if len(dropdown_options) >= 3 else None,
                clearable=False,
                className='dcc-dropdown'
            ),
            dcc.Dropdown(
                id='wb-ranking-year',
                options=[],  # Will be populated dynamically via callbacks
                value=None,  # Default value set dynamically
                clearable=False,
                className='dcc-dropdown'
            ),
            dcc.Graph(id='wb-bar-plot', className='dcc-graph'),
            html.H3('Select Number of Countries:'),
            dcc.Slider(
                id='wb-num-countries',
                min=10,
                max=len(wdi_df['Country'].unique()),
                step=10,
                value=10,
                marks={i: str(i) for i in range(10, len(wdi_df['Country'].unique()) + 10, 10)}
            ),
            dcc.Graph(id='wb-world-map', className='dcc-graph')
        ])
    ])
    return layout


def get_monitoring_elections_layout(elections_df):
    """
    Returns the layout for the Monitoring Elections page.
    
    :param elections_df: A pandas DataFrame containing elections data.
                         Expected to have at least a 'year' column.
    """
    # Get the list of unique years and set the default to the latest year
    years = sorted(elections_df['year'].unique())
    default_year = years[-1] if years else None

    layout = html.Div([
        html.H1("Monitoring Elections"),
        dcc.Dropdown(
            id='year-dropdown',
            className='dcc-dropdown',
            options=[{'label': str(year), 'value': year} for year in years],
            value=default_year,
            clearable=False,
            placeholder="Select a year"
        ),
        html.Div(id='tables-container')  # This container will be filled by a callback with monthly tables
    ])
    return layout
