from dash import dcc, html, dash_table
from utils.date_utils import transform_date_to_day_first
from utils.data_loader import load_all_data

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


def get_monitoring_acled_layout(frequencies):

    # Load initial data using a default frequency (e.g., "daily")
    data = load_all_data("daily")
    available_dates = sorted(data['event_date'].unique())
    default_date = available_dates[-1] if available_dates else None
    unavailable_cols = [
        'event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon',
        'month', 'quarter', 'week', 'violence index_exp_moving_avg', 'General',
        'Legislative', 'Local', 'Parliamentary', 'Presidential', 'Referendum', 'holiday'
    ]
    column_options = [{'label': col, 'value': col} for col in data.columns if col not in unavailable_cols]
    country_options = [{'label': c, 'value': c} for c in sorted(data['country'].unique())]

    layout = html.Div([
        html.H1('Explore Events', style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='ranking-column',
                    options=column_options,
                    value='violence index',
                    clearable=False,
                    className='dcc-dropdown'
                ),
                dcc.Dropdown(
                    id='evolution-country',
                    options=country_options,
                    value=['Afghanistan'],
                    multi=True,
                    clearable=False,
                    className='dcc-dropdown'
                ),
            ], style={'flex': '1', 'padding': '10px'}),
            html.Div([
                dcc.Dropdown(
                    id='ranking-date',
                    options=[{'label': date, 'value': date} for date in available_dates],
                    value=default_date,
                    clearable=False,
                    className='dcc-dropdown'
                ),
                dcc.Dropdown(
                    id='frequency',
                    options=[{'label': freq, 'value': freq} for freq in frequencies],
                    value="daily",
                    clearable=False,
                    className='dcc-dropdown'
                ),
            ], style={'flex': '1', 'padding': '10px'}),
        ], style={'display': 'flex', 'width': '100%', 'gap': '20px'}),
        html.Div(
            id='selected-countries-text',
            style={'textAlign': 'center', 'padding': '5px', 'fontSize': '16px'}
        ),
        # Bar plot and map
        html.Div([
            html.Div([
                html.H2('Country Ranking', style={'textAlign': 'left'}),
                dcc.Graph(id='bar-plot', className='dcc-graph'),
            ], style={'flex': '1', 'padding': '5px'}),
            html.Div([
                html.H2('Event Map', style={'textAlign': 'left'}),
                dcc.Graph(id='world-map', className='dcc-graph'),
            ], style={'flex': '1', 'padding': '5px'}),
        ], style={'display': 'flex', 'flex-wrap': 'wrap', 'width': '100%', 'gap': '5px'}),
        # Line plot
        html.Div([
            html.H2('Historical Trend', style={'textAlign': 'left'}),
            dcc.Graph(id='line-plot', className='dcc-graph'),
        ], style={'flex': '1', 'padding': '5px'}),
        # Table
        html.Div([
            html.H2('Event Table', style={'textAlign': 'left'}),
            dash_table.DataTable(
                id='data-table',
                style_data={'color': 'white', 'backgroundColor': 'rgb(50, 50, 50)'},
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_cell={
                    'textAlign': 'left',
                    'height': 'auto',
                    'minWidth': '90px',
                    'width': '180px',
                    'maxWidth': '180px',
                    'whiteSpace': 'normal'
                },
                style_data_conditional=[]
            ),
        ], style={'width': '100%', 'padding': '10px'})
    ], style={'width': '99%', 'margin': '0 auto'})
    
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
            html.Div([
            html.Div([
                dcc.Graph(id='wb-bar-plot', className='dcc-graph'),
            html.H3('Select Number of Countries:'),
            dcc.Slider(
                id='wb-num-countries',
                min=10,
                max=len(default_df[country_col].unique()),
                step=10,
                value=10,
                marks={i: str(i) for i in range(10, len(default_df[country_col].unique()) + 10, 10)}
            )
            ], style={'flex': '1', 'padding': '10px'}),
            html.Div([
                dcc.Graph(id='wb-world-map', className='dcc-graph')
            ], style={'flex': '1', 'padding': '10px'}),
        ], style={'display': 'flex', 'width': '100%', 'gap': '20px'}),
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
