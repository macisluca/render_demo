import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import os
import numpy as np
import re
from datetime import datetime, timedelta

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# Paths to the relevant folders
DATA_PATH = 'data/interim/data_ready/'
FORECAST_PATH = 'models/TiDE/predictions/sampling/'
FORECAST_HTML_PATH = 'docs/figures/operative/TiDE/default/'
ISO3_PATH = 'data/raw/ACLED_coverage_ISO3.csv'

# Helper function to load CSV data
def load_all_data():
    files = [f for f in os.listdir(DATA_PATH) if f.endswith('.csv')]
    dfs = [pd.read_csv(os.path.join(DATA_PATH, file)) for file in files]
    return pd.concat(dfs, ignore_index=True)

# Helper function to load forecast data
def load_forecast_data(date_folder):
    folder_path = os.path.join(FORECAST_PATH, date_folder)
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    dfs = [pd.read_csv(os.path.join(folder_path, file)) for file in files]
    return pd.concat(dfs, ignore_index=True)

# Helper function to load crisis data
def load_crisis_data(date):
    CRISIS_REPORT_PATH = f'reports/tables/operative/TiDE/UDC_{date}/'
    files = [f for f in os.listdir(CRISIS_REPORT_PATH) if f.endswith('.csv')]
    dfs = [pd.read_csv(os.path.join(CRISIS_REPORT_PATH, file)) for file in files]
    return pd.concat(dfs, ignore_index=True)

# Helper function to transform dates into format DD/MM/YYYY
def transform_date_to_day_first(date_input):
    """
    Transforms a date input into the format DD/MM/YYYY.
    
    :param date_input: A date string or datetime object.
    :return: A string representing the date in DD/MM/YYYY format.
    """
    # If the input is a string, convert it to a datetime object
    if isinstance(date_input, str):
        try:
            # Attempt to parse the string in a common format (e.g., YYYY-MM-DD)
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD format."
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        return "Invalid input. Please provide a string or datetime object."

    # Return the date formatted as DD/MM/YYYY
    return date_obj.strftime("%d/%m/%Y")


# Load initial data
data = load_all_data()

# Extract available dates and other options
available_dates = sorted(data['event_date'].unique())[:-12]
default_date = available_dates[-1]
available_forecast_dates = sorted([f for f in os.listdir(FORECAST_PATH) if os.path.isdir(os.path.join(FORECAST_PATH, f))], reverse=True)
default_forecast_date = available_forecast_dates[0]

# Load initial crisis data
crisis_data = load_crisis_data(default_forecast_date)
crisis_weeks = list(sorted(crisis_data['end of the week'].unique()))

# Load the WDI dataframe and ACLED_coverage_ISO3 csv
directory_wdi = "data/WDI/"
# List all CSV files in the directory
csv_files = [os.path.join(directory_wdi, file) for file in os.listdir(directory_wdi) if file.endswith('.csv')]
# Concatenate all CSV files into a single DataFrame
wdi_raw_df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)
acled_coverage_iso3_df = pd.read_csv("data/raw/ACLED_coverage_ISO3.csv")

# Merge to add the "Country" column
wdi_df = pd.merge(
    wdi_raw_df,
    acled_coverage_iso3_df[['ISO_3166-3', 'Country']],
    how='left',
    left_on='ISO_3',
    right_on='ISO_3166-3'
)

# Event Raw Data
event_data = pd.read_csv('data/last_month_acled.csv')
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

# Navbar layout with dropdown menu for Monitoring
navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Monitoring ACLED", href="/monitoring/acled"),
                dbc.DropdownMenuItem("Monitoring World Bank Data", href="/monitoring/worldbank"),
            ],
            nav=True,
            in_navbar=True,
            label="Monitoring",
        ),
        dbc.NavItem(dbc.NavLink("Forecasting", href="/forecasting")),
    ],
    brand="Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
)

# Monitoring layout
monitoring_acled_layout = html.Div([
    html.H1('Monitoring ACLED Dashboard'),
    html.Div(className='container', children=[
        html.H2('Global Daily Events Map'),
        html.H3('Select a date, and the map will display the events that occurred on that day.'),
        dcc.Dropdown(id='map-date', options=[{'label': transform_date_to_day_first(date), 'value': date} for date in available_event_dates], value=default_event_date, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='event-map', className='dcc-graph'),
        html.H2('Ranking by Variable on a weekly basis'),
        dcc.Dropdown(id='ranking-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
        dcc.Dropdown(id='ranking-date', options=[{'label': transform_date_to_day_first(date), 'value': date} for date in available_dates], value=default_date, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='bar-plot', className='dcc-graph'),
        html.H3('Select number of countries:'),
        dcc.Slider(id='num-countries', min=10, max=235, step=10, value=10, marks={i: str(i) for i in range(10, 236, 10)}),
        dcc.Graph(id='world-map', className='dcc-graph'),
        html.H3("Data source: ACLED (www.acleddata.com). Accessed on November 13th, 2024."),
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
        html.H3("Data source: ACLED (www.acleddata.com). Accessed on November 13th, 2024.")
    ]),
    html.Footer(
        [
        "Modifications from ACLED Data: Violence index calculated based on the paper ",
        html.A("Violence Index: a new data-driven proposal to conflict monitoring", href="https://dx.doi.org/10.4995/CARMA2024.2024.17831", target="_blank"),
        ],
    style={'textAlign': 'center', 'fontSize': 'small', 'padding': '10px'}
    ),
])

# Monitoring World Bank Data layout
monitoring_worldbank_layout = html.Div([
    html.H1('Monitoring World Bank Data Dashboard'),
    html.Div(className='container', children=[
        html.H2('Ranking by Variable on an annual basis'),
        dcc.Dropdown(
            id='wb-ranking-column',
            options=[{'label': col, 'value': col} for col in wdi_df.columns if col not in ['ISO_3', 'ISO_3166-3', 'Country', 'year']],
            value=wdi_df.columns[2],  # Default to the first data column
            clearable=False,
            className='dcc-dropdown'
        ),
        dcc.Dropdown(
            id='wb-ranking-year',
            options=[],  # Initially empty; populated dynamically
            value=None,  # Default will be set dynamically
            clearable=False,
            className='dcc-dropdown'
        ),
        dcc.Graph(id='wb-bar-plot', className='dcc-graph'),
        html.H3('Select number of countries:'),
        dcc.Slider(
            id='wb-num-countries',
            min=10,
            max=len(wdi_df['Country'].unique()),
            step=10,
            value=10,
            marks={i: str(i) for i in range(10, len(wdi_df['Country'].unique()) + 10, 10)}
        ),
        dcc.Graph(id='wb-world-map', className='dcc-graph')
    ]),
])


# Forecasting layout
forecasting_layout = html.Div([
    html.H1('Forecasting Dashboard'),
    html.H2('Forecasting of most violent countries'),
    dcc.Dropdown(id='forecast-date', options=[{'label': transform_date_to_day_first(date), 'value': date} for date in available_forecast_dates], value=default_forecast_date, clearable=False, className='dcc-dropdown'),
    html.H3('Select forecasted week:'),
    dcc.Slider(id='forecast-slider', min=0, max=11, step=1, value=0, marks={i: f'Forecast {i+1}' for i in range(12)}),
    html.H3('Select outcome level:'),
    dcc.Slider(id='percentile-slider', min=0, max=100, step=1, value=50, marks={i: str(i) for i in range(0, 101, 10)}),
    dcc.Graph(id='forecast-bar-plot', className='dcc-graph'),
    html.H3('Select number of countries:'),
    dcc.Slider(id='num-forecasted-countries', min=10, max=160, step=10, value=10, marks={i: str(i) for i in range(10, 160, 10)}),
    dcc.Graph(id='forecast-world-map', className='dcc-graph'),
    html.H2('Select Country Violence Forecasts'),
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

# Main layout
app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    html.Div(id="page-content")
])

# Page routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/monitoring/acled':
        return monitoring_acled_layout
    elif pathname == '/monitoring/worldbank':
        return monitoring_worldbank_layout
    elif pathname == '/forecasting':
        return forecasting_layout
    else:
        return monitoring_acled_layout


# Callback for event map
@app.callback(
    [Output('event-map', 'figure')],  # Expecting a list or tuple of outputs
    [Input('map-date', 'value')]
)

def update_event_map(selected_date):
    # Filter data for the selected date
    filtered_df = event_data[event_data['event_date'] == selected_date]

    # Group by latitude, longitude, and event_type
    grouped = filtered_df.groupby(['latitude', 'longitude', 'event_type']).agg(
        numerosity=('event_type', 'size'),  # Count the number of events in the group
        fatalities=('fatalities', 'sum'),  # Sum the fatalities for each group
        actors=('actor1', lambda x: ', '.join(sorted(set(x)))),  # Concatenate unique actor1 values
        #admin1=('admin1', lambda x: ', '.join(sorted(set(x)))),  # Concatenate unique admin1 values
        #admin2=('admin2', lambda x: ', '.join(sorted(set(x)))),  # Concatenate unique admin2 values
        events=('sub_event_type', lambda x: ', '.join(sorted(set(x)))),   # Concatenate unique sub_event_type values
        description=('notes', lambda x: '/'.join(sorted(set(x)))),   # Concatenate unique notes values
    ).reset_index()

    # Apply the function to the 'description' column
    grouped['description'] = grouped['description'].apply(add_br_to_description)

    # Generate map with Plotly Express
    fig = px.scatter_mapbox(grouped,
                            lat='latitude',
                            lon='longitude',
                            size='numerosity',  # Circle size based on count
                            color='event_type',  # Color based on event_type
                            hover_name='event_type',
                            hover_data={'actors': True, 'events': True, 'numerosity': True, 'fatalities':True, 'description':True, 'event_type': False, 'latitude': False, 'longitude': False},
                            zoom=1.5,
                            opacity=0.5,
                            template='plotly_dark')

    # Update map style
    fig.update_layout(mapbox_style="carto-positron")

    # Add ACLED attribution annotation
    fig.add_annotation(
        text="Data source: ACLED; accessed November 13th, 2024. See www.acleddata.com for details.",
        xref="paper", yref="paper",
        x=0.5, y=-0.1, showarrow=False,
        font=dict(size=10, color="white")
    )

    return [fig]

def add_br_to_description(description):
    # First, add <br><br> after every `/`
    description_with_slashes = description.replace('/', '<br><br>')
    
    # Insert <br> at the first space after every 50 characters
    def insert_br_at_space(text, limit):
        pattern = r'(.{'+str(limit)+r'}\S*)\s'  # Match at least 'limit' characters, followed by a space
        return re.sub(pattern, r'\1<br> ', text)  # Replace the match with the text and insert <br> before the space

    # Apply the function, inserting <br> after 50 characters
    description_with_breaks = insert_br_at_space(description_with_slashes, 50)

    return description_with_breaks

# Callback for bar plot and world map
@app.callback(
    [Output('bar-plot', 'figure'),
     Output('world-map', 'figure')],
    [Input('ranking-column', 'value'),
     Input('ranking-date', 'value'),
     Input('num-countries', 'value')]
)

def update_bar_and_map(selected_column, selected_date, num_countries):
    # Filter the data for the selected date
    filtered_data = data[data['event_date'] == selected_date]
    # Sort countries by the selected column
    sorted_data = filtered_data.sort_values(by=selected_column, ascending=False).head(num_countries)
    # Convert string to date
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    # Subtract 6 days
    six_days_before = date_obj - timedelta(days=6)
    six_days_before_str = six_days_before.strftime("%Y-%m-%d")
    # Create the bar plot
    bar_fig = px.bar(sorted_data, x='country', y=selected_column, template='plotly_dark',
                     color=selected_column, color_continuous_scale='orrd',
                 title=f'Top {num_countries} countries by {selected_column} from {transform_date_to_day_first(six_days_before_str)} to {transform_date_to_day_first(selected_date)}')
    
    # Create the world map
    map_fig = px.choropleth(
        filtered_data,
        locations="ISO_3",
        color=selected_column,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale=px.colors.sequential.OrRd,
        title=selected_column + " by Country",
        template='plotly_dark'
    )
    map_fig.update_layout(autosize=False, margin = dict(l=0,r=0,b=0,t=0,pad=4,autoexpand=True),
        title_text=selected_column + ' by Country',
        geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth')
    )
    return bar_fig, map_fig


# Callback for line plot and data table
@app.callback(
    [Output('line-plot', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns')],
    [Input('evolution-column', 'value'),
     Input('evolution-country', 'value'),
     Input('plot-date', 'value')]
)

def update_line_plot_and_table(selected_column, selected_countries, plot_date):
    # Create an empty DataFrame to collect data for selected countries
    combined_data = pd.DataFrame()
    
    # Load data for each selected country and append it to combined_data
    for country in selected_countries:
        country_data = pd.read_csv(os.path.join(DATA_PATH, f'{country}.csv'))
        country_data['country'] = country
        combined_data = pd.concat([combined_data, country_data])

    # Create the line plot showing the evolution of the selected column for each country
    line_fig = px.line(combined_data, x='event_date', y=selected_column, color='country', template='plotly_dark',
                  title=f'{selected_column} over time for {", ".join(selected_countries)}')
    
    # Add circle markers for each country at the plot_date
    for country in selected_countries:
        country_data = combined_data[combined_data['country'] == country]
        
        # Find the y-value (selected_column value) at the plot_date
        y_value = country_data.loc[country_data['event_date'] == plot_date, selected_column].values[0]
        
        # Add a scatter trace for the marker at the specific point
        line_fig.add_scatter(x=[plot_date], y=[y_value], mode='markers',
                             marker=dict(color='white', size=10, symbol='circle'),
                             name=f'{country} date')
    
    # Prepare the table data for the selected countries
    table_data = []
    for country in selected_countries:
        country_data = combined_data[combined_data['country'] == country]
        latest_values = country_data.loc[country_data['event_date'] == plot_date].to_dict('records')[0]
        table_data.append(latest_values)

    new_table_data = []
    for col in combined_data.columns:
        if col in unavailable_table_cols:
            continue
        string_col = col.replace("_", ": ")
        string_col = string_col.replace("/", ", ")
        string_col = 'Violence index 1 Year moving average' if col == 'violence index_moving_avg' else string_col
        new_row = {'Country': string_col}
        for i, country in enumerate(selected_countries):
            new_row[country] = table_data[i][col]
            if isinstance(table_data[i][col], float):
                new_row[country] = np.round(table_data[i][col],0)
        # Append value if is not 0 in 1 of the countries
        for i, country in enumerate(selected_countries):
            append_value = False
            if table_data[i][col] not in [0, '0']:
                append_value = True
            if append_value:
                new_table_data.append(new_row)

    
    columns_default = [{'name':'Country', 'id':'Country'}]
    columns = [{'name':country, 'id':country} for country in selected_countries]
    columns = columns_default + columns

    return line_fig, new_table_data, columns


# WDI: Create a filtered year dropdown
@app.callback(
    Output('wb-ranking-year', 'options'),
    Input('wb-ranking-column', 'value')  # Dropdown for selecting variable
)
def update_year_options(selected_column):
    # Filter the years based on the selected column
    valid_years = wdi_df.loc[wdi_df[selected_column].notna(), 'year'].unique()
    valid_years = sorted(valid_years)
    return [{'label': year, 'value': year} for year in valid_years]

# Example: Default value for the dropdown
@app.callback(
    Output('wb-ranking-year', 'value'),
    Input('wb-ranking-year', 'options')
)
def set_default_year(year_options):
    # Default to the most recent year in the filtered options
    return year_options[-1]['value'] if year_options else None

# Callbacks for the Bar Plot and World Map WDI
@app.callback(
    [Output('wb-bar-plot', 'figure'),
     Output('wb-world-map', 'figure')],
    [Input('wb-ranking-column', 'value'),
     Input('wb-ranking-year', 'value'),
     Input('wb-num-countries', 'value')]
)
def update_world_bank_graphs(selected_column, selected_year, num_countries):
    # Filter data by year
    filtered_data = wdi_df[wdi_df['year'] == selected_year]

    # Sort data by the selected column and select top countries
    sorted_data = filtered_data.sort_values(by=selected_column, ascending=False).head(num_countries)

    # Create the bar plot
    bar_fig = px.bar(
        sorted_data,
        x='Country',
        y=selected_column,
        template='plotly_dark',
        color=selected_column,
        color_continuous_scale='orrd',
        title=f'Top {num_countries} countries by {selected_column} in {selected_year}'
    )
    bar_fig.update_layout(coloraxis_colorbar_title_text="")  # Remove color bar title

    # Create the world map
    map_fig = px.choropleth(
        filtered_data,
        locations="ISO_3",
        color=selected_column,
        hover_name="Country",
        projection="natural earth",
        color_continuous_scale=px.colors.sequential.OrRd,
        title=f'{selected_column} by Country in {selected_year}',
        template='plotly_dark'
    )
    map_fig.update_layout(coloraxis_colorbar_title_text="")  # Remove color bar title


    return bar_fig, map_fig

# Callbacks Forecasting
@app.callback(
    [Output('forecast-bar-plot', 'figure'),
     Output('forecast-world-map', 'figure')],
    [Input('forecast-date', 'value'),
     Input('forecast-slider', 'value'),
     Input('percentile-slider', 'value'),
     Input('num-forecasted-countries', 'value')])

def update_forecasting_dashboard(selected_date, forecast_step, percentile, num_forecasted_countries):
    forecast_data = load_forecast_data(selected_date)
    iso3_data = pd.read_csv(ISO3_PATH)
    forecast_data = forecast_data.merge(iso3_data[['Country', 'ISO_3166-3']], left_on='country', right_on='Country')
    forecast_data.rename(columns={'ISO_3166-3': 'ISO_3'}, inplace=True)
    forecast_data.drop(columns=['Country'], inplace=True)
    forecast_data = forecast_data[forecast_data['forecast'] == forecast_data['forecast'].unique()[forecast_step]]
    outcome_percentiles = forecast_data.groupby('ISO_3')['outcome'].quantile(percentile / 100).reset_index()
    outcome_sorted_percentiles = outcome_percentiles.sort_values(by='outcome', ascending=False).head(num_forecasted_countries)

    bar_fig = px.bar(outcome_sorted_percentiles, x='ISO_3', y='outcome', template='plotly_dark', color='outcome', color_continuous_scale='orrd')
    map_fig = px.choropleth(outcome_percentiles, locations="ISO_3", color="outcome", hover_name="ISO_3", projection="natural earth", color_continuous_scale=px.colors.sequential.OrRd, template='plotly_dark')
    map_fig.update_layout(autosize=False, margin=dict(l=0, r=0, b=0, t=0))#paper_bgcolor="#F6F5EC", plot_bgcolor="#F6F5EC"
    #map_fig.update_geos(fitbounds='locations', visible=False, bgcolor='#F6F5EC')
    return bar_fig, map_fig


# Callbacks for embedding forecast HTML plots
@app.callback(Output('forecast-line-plot', 'srcDoc'),
              [Input('forecast-country', 'value')])

def update_forecast_line_plot(country):
    html_file_path = os.path.join(FORECAST_HTML_PATH, f'{country}.html')
    with open(html_file_path, 'r') as file:
        return file.read()

# Callback for crisis map
@app.callback(Output('crisis-world-map', 'figure'),
              [Input('crisis-end-week', 'value'),
               Input('crisis-type', 'value')])

def update_crisis_map(selected_week, crisis_type):
    crisis_data = load_crisis_data(default_forecast_date)
    filtered_data = crisis_data[crisis_data['end of the week'] == selected_week]
    world_map_fig = px.choropleth(filtered_data, locations="iso3", color=crisis_type, hover_name="country", projection="natural earth", color_continuous_scale=px.colors.sequential.OrRd, template='plotly_dark')
    world_map_fig.update_layout(autosize=False, margin=dict(l=0, r=0, b=0, t=0))
    return world_map_fig

# Start the app
if __name__ == '__main__':
    app.run_server(debug=False)
