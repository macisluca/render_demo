import pandas as pd
import numpy as np
import os
import plotly.express as px
from dash.dependencies import Input, Output
from datetime import datetime, timedelta
from utils.date_utils import transform_date_to_day_first, add_br_to_description
from app_instance import app
from utils.data_loader import (
    load_all_data,
    load_event_data, 
    load_ACLED_event_data,
    DATA_PATH
)


event_data = load_event_data()
acled_event_data = load_ACLED_event_data()

# Callback for event map
@app.callback(
    Output('event-map', 'figure'),
    [Input('map-date', 'value')]
)
def update_event_map(selected_date):
    # Convert selected_date to a date object if it's a string
    if isinstance(selected_date, str):
        selected_date = pd.to_datetime(selected_date).date()
    
    # Filter data for the selected date
    filtered_df = event_data[event_data['event_date'] == selected_date].dropna(subset=['latitude', 'longitude'])

    # Group by latitude, longitude, and event_type.
    # For text aggregation, we drop missing values and convert each element to string.
    grouped = filtered_df.groupby(['latitude', 'longitude', 'event_type'], as_index=False).agg(
        actors=('actor', lambda x: ', '.join(sorted(map(str, set(x.dropna()))))),
        recipients=('recipient', lambda x: ', '.join(sorted(map(str, set(x.dropna()))))),
        description=('description', lambda x: ' / '.join(sorted(map(str, set(x.dropna())))))
    ).reset_index()

    # Apply the function to the 'description' column
    grouped['description'] = grouped['description'].apply(add_br_to_description)
    # Create a scatter mapbox plot with color coding based on event_type
    fig = px.scatter_mapbox(
        grouped,
        lat='latitude',
        lon='longitude',
        color='event_type',
        hover_name='event_type',
        hover_data={
            'actors': True,
            'recipients': True,
            'description': True,
            'latitude': False,
            'longitude': False
        },
        zoom=2,
        opacity=0.7,
        height=600,
        template='plotly_dark'
    )

    # Update map style
    fig.update_layout(
        mapbox_style="carto-positron",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_traces(marker=dict(size=10))

    return fig


# Callback for ACLED event map
@app.callback(
    [Output('acled-event-map', 'figure')],  # Expecting a list or tuple of outputs
    [Input('acled-map-date', 'value')]
)

def update_acled_event_map(selected_date):
    # Filter data for the selected date
    filtered_df = acled_event_data[acled_event_data['event_date'] == selected_date]

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
    fig.update_layout(mapbox_style="carto-positron",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ))

    # Add ACLED attribution annotation
    fig.add_annotation(
        text="Data source: ACLED; accessed November 13th, 2024. See www.acleddata.com for details.",
        xref="paper", yref="paper",
        x=0.5, y=-0.1, showarrow=False,
        font=dict(size=10, color="white")
    )

    return [fig]



data = load_all_data()
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
    bar_fig.update_layout(coloraxis_colorbar_title_text="", )  # Remove color bar title

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
        geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth'),
        coloraxis_colorbar_title_text=""  # Remove color bar title
    )
    return bar_fig, map_fig


unavailable_table_cols = ['country', 'month', 'quarter', 'week', 'event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon', 'violence index_exp_moving_avg', 'General', 'Legislative', 'Local', 'Parliamentary', 'Presidential', 'Referendum', 'holiday']
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

    line_fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,))
    
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
