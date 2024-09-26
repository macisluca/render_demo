import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import os
import dash_table

# Path to the CSV files
DATA_PATH = 'data/interim/data_ready/'

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# Helper function to load all CSVs and concatenate into a single DataFrame
def load_all_data():
    files = [f for f in os.listdir(DATA_PATH) if f.endswith('.csv')]
    dfs = []
    for file in files:
        df = pd.read_csv(os.path.join(DATA_PATH, file))
        df['country'] = file.split('.')[0]  # Add a 'country' column based on the file name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Load the data initially
data = load_all_data()

# Dropdown options for column selection (assuming all CSVs have similar columns)
unavailable_cols = ['event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon', 'month', 'quarter', 'week']
unavailable_table_cols = ['country', 'month', 'quarter', 'week']
column_options = [{'label': col, 'value': col} for col in data.columns if col not in unavailable_cols]

# Available dates in the dataset
available_dates = sorted(data['event_date'].unique())
available_dates = available_dates[:-12]
default_date = available_dates[-1]  # Set the latest date as default

# Define the navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Monitoring", href="/monitoring")),
        dbc.NavItem(dbc.NavLink("Forecasting", href="/forecasting")),
    ],
    brand="Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
)

# Define the layout for the Monitoring page
monitoring_layout = html.Div([
    html.H1('Monitoring Dashboard'),
    html.Div(className='container', children=[
        html.Div(className='monitoring-section', children=[
            html.H2('Ranking by Variable and Date'),
            html.Div(className='dcc-dropdown', children=[
                dcc.Dropdown(id='ranking-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
                dcc.Dropdown(id='ranking-date', options=[{'label': date, 'value': date} for date in available_dates], 
                         value=default_date, clearable=False, className='dcc-dropdown'),
            ]),
            dcc.Graph(id='bar-plot', className='dcc-graph'),
            dcc.Slider(id='num-countries', min=10, max=235, step=10, value=10,
                marks={i: str(i) for i in range(10, 236, 10)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            dcc.Graph(id='world-map', className='dcc-graph'),
        ]),

        html.Div(className='monitoring-section', children=[
            html.H2('Countries Stats Over Time'),
            dcc.Dropdown(id='evolution-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
            dcc.Dropdown(id='evolution-country',
                         options=[{'label': c, 'value': c} for c in sorted(data['country'].unique())],
                         value=['Afghanistan'], multi=True, clearable=False, className='dcc-dropdown'),
            dcc.Graph(id='line-plot', className='dcc-graph'),
            html.Div(className='table', children=[
                dash_table.DataTable(id='data-table',
                                     style_data={'color': 'white','backgroundColor': 'rgb(50, 50, 50)'},
                                     style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
                                     style_cell={'height': 'auto', 'minWidth': '90px', 'width': '180px', 'maxWidth': '180px', 'whiteSpace': 'normal'}
                                    )
            ]),
        ]),
    ]),
])



# Path to the TiDE predictions folder
FORECAST_PATH = 'models/TiDE/predictions/sampling/'
# Path to the df with iso3 and country names
ISO3_PATH = 'data/raw/ACLED_coverage_ISO3.csv'

# Helper function to load the forecast data based on the selected folder (date)
def load_forecast_data(date_folder):
    folder_path = os.path.join(FORECAST_PATH, date_folder)
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    dfs = []
    for file in files:
        df = pd.read_csv(os.path.join(folder_path, file))
        df['country'] = file.split('.')[0]  # Add a 'country' column based on the file name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Get available forecast dates (folders)
available_forecast_dates = sorted([f for f in os.listdir(FORECAST_PATH) if os.path.isdir(os.path.join(FORECAST_PATH, f))], reverse=True)
default_forecast_date = available_forecast_dates[0]  # Default to the most recent folder


# App layout for forecasting dashboard
forecasting_layout = html.Div([
    html.H1('Forecasting Dashboard'),

    # Date selection dropdown
    dcc.Dropdown(
        id='forecast-date',
        options=[{'label': date, 'value': date} for date in available_forecast_dates],
        value=default_forecast_date,  # Default to the most recent date
        clearable=False,
        className='dcc-dropdown'
    ),

    # Slider for forecast dates (12 forecast dates)
    dcc.Slider(
        id='forecast-slider',
        min=0, max=11, step=1, value=0,
        marks={i: f'Forecast {i+1}' for i in range(12)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    # Slider for percentile selection (0 to 100)
    dcc.Slider(
        id='percentile-slider',
        min=0, max=100, step=1, value=50,
        marks={i: str(i) for i in range(0, 101, 10)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    # Bar plot for country outcomes
    dcc.Graph(id='forecast-bar-plot', className='dcc-graph'),

    # World map for country outcomes
    dcc.Graph(id='forecast-world-map', className='dcc-graph')
])

# Callback for the bar plot and world map
@app.callback(
    [Output('forecast-bar-plot', 'figure'),
     Output('forecast-world-map', 'figure')],
    [Input('forecast-date', 'value'),
     Input('forecast-slider', 'value'),
     Input('percentile-slider', 'value')]
)
def update_forecasting_dashboard(selected_date, forecast_step, percentile):
    # Load forecast data for the selected folder
    forecast_data = load_forecast_data(selected_date)
    country_names_iso3_data = pd.read_csv(ISO3_PATH)
    # Merge the forecast_data with country_names_iso3_data on the country name
    forecast_data = forecast_data.merge(country_names_iso3_data[['Country', 'ISO_3166-3']], 
                                        left_on='country', 
                                        right_on='Country', 
                                        how='left')
    # Rename the ISO_3166-3 column to ISO_3
    forecast_data.rename(columns={'ISO_3166-3': 'ISO_3'}, inplace=True)
    # Optionally, drop the redundant 'Country' column from the merge
    forecast_data.drop(columns=['Country'], inplace=True)
    print(forecast_data)

    # Filter for the selected forecast step
    forecast_data = forecast_data[forecast_data['forecast'] == forecast_data['forecast'].unique()[forecast_step]]

    # Calculate the percentile of the outcome values for each ISO_3
    outcome_percentiles = forecast_data.groupby('ISO_3')['outcome'].quantile(percentile / 100).reset_index()
    sorted_outcomes = outcome_percentiles.sort_values(by='outcome', ascending=False)

    # Bar plot for country outcomes
    bar_fig = px.bar(sorted_outcomes, x='ISO_3', y='outcome', template='plotly_dark',
                     color='outcome', color_continuous_scale='mint',
                     title=f'Forecast Outcomes for {forecast_data["forecast"].unique()[0]} at {percentile}th Percentile')

    # World map for country outcomes
    map_fig = px.choropleth(
        outcome_percentiles,
        locations="ISO_3",
        color="outcome",
        hover_name="ISO_3",
        projection="natural earth",
        color_continuous_scale=px.colors.sequential.Mint,
        title=f'Forecast Outcomes for {forecast_data["forecast"].unique()[0]} at {percentile}th Percentile',
        template='plotly_dark'
    )

    map_fig.update_layout(autosize=False, margin = dict(l=0,r=0,b=0,t=0,pad=4,autoexpand=True),
        title_text=f'Forecast Outcomes for {forecast_data["forecast"].unique()[0]} at {percentile}th Percentile',
        geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular')
    )

    return bar_fig, map_fig







# App layout with navbar and page content
app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    html.Div(id="page-content")  # This will be updated based on the selected page
])

# Update page content based on the URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/monitoring':
        return monitoring_layout
    elif pathname == '/forecasting':
        return forecasting_layout
    else:
        return monitoring_layout  # Default to Monitoring if no path is specified

# Define other callbacks (e.g., for updating plots) here...
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
    
    # Create the bar plot
    bar_fig = px.bar(sorted_data, x='country', y=selected_column, template='plotly_dark',
                     color=selected_column, color_continuous_scale='mint',
                 title=f'Top {num_countries} countries by {selected_column} on {selected_date}')
    
    
    # Create the world map
    map_fig = px.choropleth(
        filtered_data,
        locations="ISO_3",
        color=selected_column,
        hover_name="country",
        projection="natural earth",
        color_continuous_scale=px.colors.sequential.Mint,
        title=selected_column + " by Country",
        template='plotly_dark'
    )
    map_fig.update_layout(autosize=False, margin = dict(l=0,r=0,b=0,t=0,pad=4,autoexpand=True),
        title_text=selected_column + ' by Country',
        geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular')
    )

    return bar_fig, map_fig

# Callback for line plot and data table
@app.callback(
    [Output('line-plot', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns')],
    [Input('evolution-column', 'value'),
     Input('evolution-country', 'value')]
)
def update_line_plot_and_table(selected_column, selected_countries):
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
    
    # Prepare the table data for the selected countries
    table_data = []
    for country in selected_countries:
        country_data = combined_data[combined_data['country'] == country]
        latest_values = country_data.loc[country_data['event_date'] == default_date].to_dict('records')[0]
        table_data.append(latest_values)

    # Format the table columns
    #columns = [{'name': col, 'id': col} for col in combined_data.columns]

    new_table_data = []
    for col in combined_data.columns:
        if col in unavailable_table_cols:
            continue
        new_row = {'Country': col}
        for i, country in enumerate(selected_countries):
            new_row[country] = table_data[i][col]
        new_table_data.append(new_row)
    
    columns_default = [{'name':'Country', 'id':'Country'}]
    columns = [{'name':country, 'id':country} for country in selected_countries]
    columns = columns_default + columns

    return line_fig, new_table_data, columns


# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
