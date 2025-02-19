from dash import dcc, html, dash_table
from utils.date_utils import transform_date_to_day_first

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


def get_monitoring_worldbank_layout(wdi_data):
    default_theme = "Economic"
    default_df = wdi_data[default_theme]
    
    # Since there is no "Country" column, we use "ISO_3" as the key
    country_col = "ISO_3"
    # Exclude non-numeric or identifier columns for ranking selection
    excluded_cols = ['ISO_3', 'ISO_3166-3', 'year']
    variable_options = [{'label': col, 'value': col} 
                        for col in default_df.columns if col not in excluded_cols]
    
    layout = html.Div([
        html.H1('Monitoring World Bank Data Dashboard'),
        html.Div(className='container', children=[
            html.H3('Select Theme:'),
            dcc.Dropdown(
                id='wb-theme',
                options=[{'label': theme, 'value': theme} for theme in sorted(wdi_data.keys())],
                value=default_theme,
                clearable=False,
                className='dcc-dropdown'
            ),
            html.H3('Select Data Mode:'),
            dcc.RadioItems(
                id='wb-data-mode',
                options=[
                    {"label": "Original Data", "value": "original"},
                    {"label": "Imputed Data", "value": "filled"}
                ],
                value="original",
                labelStyle={"display": "inline-block", "margin-right": "20px"}
            ),
            html.Div([
                html.P("Original Data: This dataset contains the raw values as reported by the World Bank. It reflects the actual reported measurements, including any missing or incomplete entries. Analyzing the original data allows you to see the data in its unaltered form, though you may need to account for gaps in the information."),
                html.P("Imputed Data: This dataset has been processed using imputation techniques to fill in missing values, resulting in a complete dataset. While imputation provides a more seamless data series for analysis, please note that the imputed values are statistical estimates and may differ from the originally reported figures.")],
                style={'fontSize': 'small', 'color': 'lightgrey', 'marginTop': '10px'}),
            html.H2('Ranking by Variable on an Annual Basis'),
            dcc.Dropdown(
                id='wb-ranking-column',
                options=variable_options,
                value=variable_options[0]['value'] if variable_options else None,
                clearable=False,
                className='dcc-dropdown'
            ),
            dcc.Dropdown(
                id='wb-ranking-year',
                options=[],  
                value=None,
                clearable=False,
                className='dcc-dropdown'
            ),
            dcc.Graph(id='wb-bar-plot', className='dcc-graph'),
            html.H3('Select Number of Countries:'),
            dcc.Slider(
                id='wb-num-countries',
                min=10,
                max=len(default_df[country_col].unique()),
                step=10,
                value=10,
                marks={i: str(i) for i in range(10, len(default_df[country_col].unique()) + 10, 10)}
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
