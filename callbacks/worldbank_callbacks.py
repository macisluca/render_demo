import plotly.express as px
import os
import pandas as pd
from dash.dependencies import Input, Output
from app_instance import app
from utils.data_loader import load_WDI_data


wdi_data = load_WDI_data()

@app.callback(
    [Output('wb-ranking-column', 'options'),
     Output('wb-ranking-column', 'value')],
    [Input('wb-theme', 'value'),
     Input('wb-data-mode', 'value')]
)
# It updates the default varuable every time you change the theme
def update_variable_options(selected_theme, data_mode):
    wdi_data = load_WDI_data(mode=data_mode)
    df = wdi_data[selected_theme]
    # Since there's no "Country" column, we exclude "ISO_3", "ISO_3166-3", and "year"
    excluded_cols = ['ISO_3', 'ISO_3166-3', 'year', 'Unnamed: 0']
    variable_options = [{'label': col, 'value': col} for col in df.columns if col not in excluded_cols]
    default_value = variable_options[0]['value'] if variable_options else None
    return variable_options, default_value

# Callback to update the year options based on selected variable, theme and data mode
@app.callback(
    Output('wb-ranking-year', 'options'),
    [Input('wb-ranking-column', 'value'),
     Input('wb-theme', 'value'),
     Input('wb-data-mode', 'value')]
)
def update_year_options(selected_column, selected_theme, data_mode):
    wdi_data = load_WDI_data(mode=data_mode)
    df = wdi_data[selected_theme]
    valid_years = df.loc[df[selected_column].notna(), 'year'].unique()
    valid_years = sorted(valid_years)
    return [{'label': year, 'value': year} for year in valid_years]

# Callback to set a default year remains unchanged:
@app.callback(
    Output('wb-ranking-year', 'value'),
    [Input('wb-ranking-year', 'options')]
)
def set_default_year(year_options):
    return year_options[-1]['value'] if year_options else None

# Callback to update bar plot and world map, using the selected theme and data mode:
@app.callback(
    [Output('wb-bar-plot', 'figure'),
     Output('wb-world-map', 'figure')],
    [Input('wb-ranking-column', 'value'),
     Input('wb-ranking-year', 'value'),
     Input('wb-num-countries', 'value'),
     Input('wb-theme', 'value'),
     Input('wb-data-mode', 'value')]
)
def update_world_bank_graphs(selected_column, selected_year, num_countries, selected_theme, data_mode):
    wdi_data = load_WDI_data(mode=data_mode)
    df = wdi_data[selected_theme]
    # Filter data by the selected year
    filtered_data = df[df['year'] == selected_year]
    
    # Sort and select top countries by the selected variable
    sorted_data = filtered_data.sort_values(by=selected_column, ascending=False).head(num_countries)
    
    # Create the bar plot
    bar_fig = px.bar(
         sorted_data,
         x='ISO_3',
         y=selected_column,
         template='plotly_dark',
         color=selected_column,
         color_continuous_scale='orrd',
         title=""
         )
    bar_fig.update_layout(
        coloraxis_colorbar_title_text="",
        xaxis_title="",
        yaxis_title="",
        yaxis=dict(showticklabels=False),
        xaxis=dict(showticklabels=False),
        coloraxis_showscale=False,
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0)
        )
    bar_fig.update_yaxes(visible=False, showticklabels=False)
    
    # Create the choropleth world map
    map_fig = px.choropleth(
         filtered_data,
         locations="ISO_3",
         color=selected_column,
         hover_name="ISO_3",
         projection="natural earth",
         color_continuous_scale=px.colors.sequential.OrRd,
         template='plotly_dark'
    )
    map_fig.update_layout(
        coloraxis_colorbar_title_text="",
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0)
        )
    
    return bar_fig, map_fig