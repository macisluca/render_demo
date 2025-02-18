import plotly.express as px
import os
import pandas as pd
from dash.dependencies import Input, Output
from app_instance import app
from utils.data_loader import load_WDI_data


wdi_df = load_WDI_data()

# Callback to update the filtered year dropdown options based on the selected variable
@app.callback(
    Output('wb-ranking-year', 'options'),
    [Input('wb-ranking-column', 'value')]
)
def update_year_options(selected_column):
    # Filter the years for which data is available for the selected column
    valid_years = wdi_df.loc[wdi_df[selected_column].notna(), 'year'].unique()
    valid_years = sorted(valid_years)
    return [{'label': year, 'value': year} for year in valid_years]

# Callback to set a default year (most recent) when the options update
@app.callback(
    Output('wb-ranking-year', 'value'),
    [Input('wb-ranking-year', 'options')]
)
def set_default_year(year_options):
    return year_options[-1]['value'] if year_options else None

# Callback to update the bar plot and world map for World Bank data
@app.callback(
    [Output('wb-bar-plot', 'figure'),
     Output('wb-world-map', 'figure')],
    [Input('wb-ranking-column', 'value'),
     Input('wb-ranking-year', 'value'),
     Input('wb-num-countries', 'value')]
)
def update_world_bank_graphs(selected_column, selected_year, num_countries):
    # Filter data by the selected year
    filtered_data = wdi_df[wdi_df['year'] == selected_year]
    
    # Sort and select top countries by the selected variable
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
    bar_fig.update_layout(coloraxis_colorbar_title_text="")
    bar_fig.update_yaxes(visible=False, showticklabels=False)
    
    # Create the choropleth world map
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
    map_fig.update_layout(coloraxis_colorbar_title_text="")
    
    return bar_fig, map_fig
