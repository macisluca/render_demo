import os
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from app_instance import app
from utils.data_loader import load_forecast_data, load_crisis_data, load_ISO3_data
from utils.date_utils import transform_date_to_day_first

FORECAST_HTML_PATH = 'docs/figures/operative/TiDE/'

# Callback for the forecasting slider
@app.callback(
    Output('forecast-slider', 'min'),  # Update the minimum value of the slider
    Output('forecast-slider', 'max'),  # Update the maximum value of the slider
    Output('forecast-slider', 'marks'),  # Update the marks of the slider
    Output('forecast-slider', 'value'),  # Update the default value of the slider
    Input('forecast-window', 'value')  # Triggered by changes in 'forecast-window'
)
def update_forecast_slider(forecast_window):

    forecast_window = int(forecast_window)
    # Set slider range dynamically based on the forecast window
    min_value = 0
    max_value = forecast_window - 1  # Maximum value is window size - 1
    marks = {i: i+1 for i in range(forecast_window)}  # Generate marks dynamically
    default_value = 0  # Default to the first week

    return min_value, max_value, marks, default_value



# Callbacks Forecasting
@app.callback(
    [Output('forecast-bar-plot', 'figure'),
     Output('forecast-world-map', 'figure')],
    [Input('forecast-variable', 'value'),
    Input('forecast-window', 'value'),
     Input('forecast-slider', 'value'),
     Input('percentile-slider', 'value'),
     Input('num-forecasted-countries', 'value')])

def update_forecasting_dashboard(selected_variable, selected_window, forecast_step, percentile, num_forecasted_countries):
    forecast_data = load_forecast_data(selected_variable, selected_window)
    iso3_data = load_ISO3_data()
    forecast_data = forecast_data.merge(iso3_data[['Country', 'ISO_3166-3']], left_on='country', right_on='Country')
    forecast_data.rename(columns={'ISO_3166-3': 'ISO_3'}, inplace=True)
    forecast_data.drop(columns=['Country'], inplace=True)
    forecast_data = forecast_data[forecast_data['forecast'] == forecast_data['forecast'].unique()[forecast_step]]
    outcome_percentiles = forecast_data.groupby('ISO_3')['outcome'].quantile(percentile / 100).reset_index()
    outcome_sorted_percentiles = outcome_percentiles.sort_values(by='outcome', ascending=False).head(num_forecasted_countries)

    forecasted_date = forecast_data['forecast'].unique()[0]

    bar_fig = px.bar(outcome_sorted_percentiles, x='ISO_3', y='outcome', template='plotly_dark', color='outcome', color_continuous_scale='orrd', title=f"Prediction for: {forecasted_date}")
    bar_fig.update_layout(coloraxis_colorbar_title_text="", )  # Remove color bar title

    map_fig = px.choropleth(outcome_percentiles, locations="ISO_3", color="outcome", hover_name="ISO_3", projection="natural earth", color_continuous_scale=px.colors.sequential.OrRd, template='plotly_dark')
    map_fig.update_layout(autosize=False, margin=dict(l=0, r=0, b=0, t=0), coloraxis_colorbar_title_text="")#paper_bgcolor="#F6F5EC", plot_bgcolor="#F6F5EC"
    #map_fig.update_geos(fitbounds='locations', visible=False, bgcolor='#F6F5EC')
    return bar_fig, map_fig


# Callbacks for embedding forecast HTML plots
@app.callback(Output('forecast-line-plot', 'srcDoc'),
              [Input('forecast-country', 'value'),
                Input('forecast-variable', 'value'),   # Triggered by changes in 'forecast-variable'
                Input('forecast-window', 'value') ])

def update_forecast_line_plot(country, forecast_variable, forecast_window):
    html_file_path = os.path.join(FORECAST_HTML_PATH, forecast_variable, forecast_window, f'{country}.html')
    with open(html_file_path, 'r') as file:
        return file.read()


# Callback to update crisis_data and crisis_weeks
@app.callback(
    Output('crisis-end-week', 'options'),   # Update the options of the 'crisis-end-week' dropdown
    Output('crisis-end-week', 'value'),    # Update the selected value of the 'crisis-end-week' dropdown
    Input('forecast-variable', 'value'),   # Triggered by changes in 'forecast-variable'
    Input('forecast-window', 'value')      # Triggered by changes in 'forecast-window'
)
def update_crisis_dropdown(forecast_variable, forecast_window):
    # Load updated crisis data based on the selected variable and window
    crisis_data = load_crisis_data(forecast_variable, forecast_window)
    
    # Update the list of unique crisis weeks
    crisis_weeks = list(sorted(crisis_data['end of the week'].unique()))
    
    # Create dropdown options and default value
    options = [{'label': transform_date_to_day_first(week), 'value': week} for week in crisis_weeks]
    default_value = crisis_weeks[0] if crisis_weeks else None
    
    return options, default_value

# Callback for crisis map
@app.callback(Output('crisis-world-map', 'figure'),
              [Input('crisis-end-week', 'value'),
              Input('forecast-variable', 'value'),
              Input('forecast-window', 'value'),
               Input('crisis-type', 'value')])

def update_crisis_map(selected_week, selected_variable, selected_window, crisis_type):
    crisis_data = load_crisis_data(selected_variable, selected_window)
    filtered_data = crisis_data[crisis_data['end of the week'] == selected_week]
    world_map_fig = px.choropleth(filtered_data, locations="iso3", color=crisis_type, hover_name="country", projection="natural earth", color_continuous_scale=px.colors.sequential.OrRd, template='plotly_dark')
    world_map_fig.update_layout(autosize=False, margin=dict(l=0, r=0, b=0, t=0), coloraxis_colorbar_title_text="")
    return world_map_fig
