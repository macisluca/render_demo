import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import os

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

# Load initial data
data = load_all_data()

# Extract available dates and other options
available_dates = sorted(data['event_date'].unique())[:-12]
default_date = available_dates[-1]
available_forecast_dates = sorted([f for f in os.listdir(FORECAST_PATH) if os.path.isdir(os.path.join(FORECAST_PATH, f))], reverse=True)
default_forecast_date = available_forecast_dates[0]

# Load initial crisis data
crisis_data = load_crisis_data(default_forecast_date)

# Column dropdown options
unavailable_cols = ['event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon', 'month', 'quarter', 'week']
unavailable_table_cols = ['country', 'month', 'quarter', 'week']
column_options = [{'label': col, 'value': col} for col in data.columns if col not in unavailable_cols]

# Crisis type dropdown options
crisis_type_options = [
    {'label': 'Probability of Extreme Crisis (%)', 'value': 'probability of extreme crisis (%)'},
    {'label': 'Probability of Severe Crisis (%)', 'value': 'probability of severe crisis (%)'},
    {'label': 'Probability of Mild Crisis (%)', 'value': 'probability of mild crisis (%)'}
]

# Navbar layout
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

# Monitoring layout
monitoring_layout = html.Div([
    html.H1('Monitoring Dashboard'),
    html.Div(className='container', children=[
        html.H2('Ranking by Variable and Date'),
        dcc.Dropdown(id='ranking-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
        dcc.Dropdown(id='ranking-date', options=[{'label': date, 'value': date} for date in available_dates], value=default_date, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='bar-plot', className='dcc-graph'),
        dcc.Slider(id='num-countries', min=10, max=235, step=10, value=10, marks={i: str(i) for i in range(10, 236, 10)}),
        dcc.Graph(id='world-map', className='dcc-graph'),
        html.H2('Countries Stats Over Time'),
        dcc.Dropdown(id='evolution-column', options=column_options, value='violence index', clearable=False, className='dcc-dropdown'),
        dcc.Dropdown(id='evolution-country', options=[{'label': c, 'value': c} for c in sorted(data['country'].unique())], value=['Afghanistan'], multi=True, clearable=False, className='dcc-dropdown'),
        dcc.Graph(id='line-plot', className='dcc-graph'),
        dash_table.DataTable(id='data-table',
            style_data={'color': 'white','backgroundColor': 'rgb(50, 50, 50)'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'height': 'auto', 'minWidth': '90px', 'width': '180px', 'maxWidth': '180px', 'whiteSpace': 'normal'}
        ),
    ]),
])

# Forecasting layout
forecasting_layout = html.Div([
    html.H1('Forecasting Dashboard'),
    dcc.Dropdown(id='forecast-date', options=[{'label': date, 'value': date} for date in available_forecast_dates], value=default_forecast_date, clearable=False, className='dcc-dropdown'),
    dcc.Slider(id='forecast-slider', min=0, max=11, step=1, value=0, marks={i: f'Forecast {i+1}' for i in range(12)}),
    dcc.Slider(id='percentile-slider', min=0, max=100, step=1, value=50, marks={i: str(i) for i in range(0, 101, 10)}),
    dcc.Graph(id='forecast-bar-plot', className='dcc-graph'),
    dcc.Slider(id='num-forecasted-countries', min=10, max=160, step=10, value=10, marks={i: str(i) for i in range(10, 160, 10)}),
    dcc.Graph(id='forecast-world-map', className='dcc-graph'),
    html.H2('Select Country Forecasts'),
    dcc.Dropdown(id='forecast-country', options=[{'label': c, 'value': c} for c in sorted(data['country'].unique())], value='Afghanistan', clearable=False, className='dcc-dropdown'),
    html.Iframe(id='forecast-line-plot', style={'width': '100%', 'height': '600px'}),
    html.H2('Crisis Map'),
    dcc.Dropdown(id='crisis-end-week', options=[{'label': week, 'value': week} for week in sorted(crisis_data['end of the week'].unique())], value='2024-09-27', clearable=False, className='dcc-dropdown'),
    dcc.Dropdown(id='crisis-type', options=crisis_type_options, value='probability of mild crisis (%)', clearable=False, className='dcc-dropdown'),
    dcc.Graph(id='crisis-world-map', className='dcc-graph'),
])

# Main layout
app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    html.Div(id="page-content")
])

# Page routing callback
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/forecasting':
        return forecasting_layout
    else:
        return monitoring_layout  # Default to monitoring


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
        geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth')
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

    bar_fig = px.bar(outcome_sorted_percentiles, x='ISO_3', y='outcome', template='plotly_dark', color='outcome', color_continuous_scale='mint')
    map_fig = px.choropleth(outcome_percentiles, locations="ISO_3", color="outcome", hover_name="ISO_3", projection="natural earth", color_continuous_scale=px.colors.sequential.Mint, template='plotly_dark')
    map_fig.update_layout(autosize=False, margin=dict(l=0, r=0, b=0, t=0))

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
    world_map_fig = px.choropleth(filtered_data, locations="iso3", color=crisis_type, hover_name="country", projection="natural earth", color_continuous_scale=px.colors.sequential.Mint, template='plotly_dark')
    world_map_fig.update_layout(autosize=False, margin=dict(l=0, r=0, b=0, t=0))
    return world_map_fig

# Start the app
if __name__ == '__main__':
    app.run_server(debug=False)
