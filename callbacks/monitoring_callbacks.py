import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from dash import html
from utils.date_utils import add_br_to_description
from app_instance import app
from utils.data_loader import (
    load_all_data,
    load_event_data, 
    load_ACLED_event_data,
    load_ISO3_data,
    DATA_PATH
)


@app.callback(
    Output('selected-countries-text', 'children'),
    [Input('evolution-country', 'value')]
)
def update_selected_countries_text(selected_countries):
    if not selected_countries:
        return ""

    # Use a Plotly qualitative color sequence for consistent colors
    color_sequence = px.colors.qualitative.Plotly

    children = []
    for i, country in enumerate(selected_countries):
        color = color_sequence[i % len(color_sequence)]
        children.append(html.Span(country, style={'color': color, 'fontWeight': 'bold'}))
        if i < len(selected_countries) - 1:
            # Append comma and space between countries
            children.append(html.Span(', ', style={'color': '#ccc'}))
    return children


# Callback to update dropdown options when frequency is changed
@app.callback(
    [Output('ranking-date', 'options'),
     Output('ranking-date', 'value'),
     Output('ranking-column', 'options'),
     Output('evolution-country', 'options')],
    [Input('frequency', 'value')]
)
def update_options_on_frequency(selected_freq):
    # Reload data based on the selected frequency
    data = load_all_data(selected_freq)
    available_dates = sorted(data['event_date'].unique())
    default_date = available_dates[-1] if available_dates else None

    # Update column options (and remove the unavailable ones)
    unavailable_cols = [
        'event_date', 'country', 'ISO_3', 'capital_lat', 'capital_lon',
        'month', 'quarter', 'week', 'violence index_exp_moving_avg', 'General',
        'Legislative', 'Local', 'Parliamentary', 'Presidential', 'Referendum', 'holiday'
    ]
    column_options = [{'label': col, 'value': col} for col in data.columns if col not in unavailable_cols]
    
    # Update country options
    country_options = [{'label': c, 'value': c} for c in sorted(data['country'].unique())]
    # Update date dropdown options
    date_options = [{'label': date, 'value': date} for date in available_dates]
    
    return date_options, default_date, column_options, country_options

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


iso3_data = load_ISO3_data()

def update_acled_event_map(iso3_data, acled_event_data, selected_column, selected_date, selected_countries):
    
    # Load the ISO-3 coordinates from the JSON file
    with open("data/raw/iso3_coordinates.json", "r") as f:
        iso3_coords = json.load(f)
    
    # Filter data for the selected date
    acled_filtered = acled_event_data[acled_event_data['event_date'] == selected_date]
    
    filtered_dfs = []
    for country in selected_countries:
        filtered_dfs.append(acled_filtered[acled_filtered['country'] == country])
    filtered_df = pd.concat(filtered_dfs)

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

    
    # Set map center and zoom level
    # If selected_iso is provided and exists in the coordinates, center on it; otherwise use a default.
    selected_iso = None
    center = {"lat": 20, "lon": 20}  # Default center (world view)
    zoom = 1
    if isinstance(selected_countries, list) and len(selected_countries)==1:
        selected_country = selected_countries[0]
        # Filter the data for the selected country and get the first occurrence of ISO_3
        selected_iso = iso3_data.loc[iso3_data['Country'] == selected_country, 'ISO_3166-3'].iloc[0] if not iso3_data.loc[iso3_data['Country'] == selected_country, 'ISO_3166-3'].empty else None
    if selected_iso and selected_iso in iso3_coords:
        center = {"lat": iso3_coords[selected_iso][0], "lon": iso3_coords[selected_iso][1]}
        zoom = 4  # Adjust zoom level as desired

    # Update layout so the map occupies its container and has no padding
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0, pad=0),
        autosize=True,
        mapbox=dict(
            style="carto-positron",  # You can change to other Mapbox styles if needed
            center=center,
            zoom=zoom
        ),
        legend=dict(
        orientation="h",
        yanchor="bottom",
        y=0.00,
        xanchor="left",
        x=0.00,),
        coloraxis_showscale=False
    )
    

    # Add ACLED attribution annotation
    fig.add_annotation(
        text="Data source: ACLED; accessed November 13th, 2024. See www.acleddata.com for details.",
        xref="paper", yref="paper",
        x=0.5, y=-0.1, showarrow=False,
        font=dict(size=10, color="white")
    )

    return fig


# Load your data once


def create_bar_plot(freq, selected_column, selected_date, selected_countries):
    """
    Create a vertical bar plot with an aggregated "Other (0)" bar for zero values,
    adding a shadow and annotation for each selected country, with consistent colors.
    """
    data = load_all_data(freq)
    # Filter and sort data for the selected date
    filtered_data = data[data['event_date'] == selected_date]
    sorted_data = filtered_data.sort_values(by=selected_column, ascending=True)
    
    # Separate nonzero and zero-value countries
    nonzero_data = sorted_data[sorted_data[selected_column] > 0]
    zero_data = sorted_data[sorted_data[selected_column] == 0]
    
    # Build x-axis labels (countries) and y-values (values)
    x_labels = list(nonzero_data['country'])
    if not zero_data.empty:
        x_labels.append("Other (0)")
    y_values = list(nonzero_data[selected_column])
    if not zero_data.empty:
        y_values.append(0)
    
    # Create vertical bar plot (main bars)
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=x_labels,
        y=y_values,
        marker_color='white',
        name=selected_column
    ))
    
    # Ensure selected_countries is a list
    if not isinstance(selected_countries, list):
        selected_countries = [selected_countries]
    
    # Define a discrete color mapping for selected countries (same as in line plot)
    color_sequence = px.colors.qualitative.Plotly
    color_mapping = {country: color_sequence[i % len(color_sequence)]
                     for i, country in enumerate(selected_countries)}
    
    max_val = sorted_data[selected_column].max()
    
    # Add a shadow trace for each selected country
    for country in selected_countries:
        if country in nonzero_data['country'].values:
            shadow_x = country
        else:
            shadow_x = "Other (0)"
        
        country_color = color_mapping.get(country, 'green')
        
        # Shadow trace: a vertical bar spanning full height, colored using the mapping
        bar_fig.add_trace(go.Bar(
            x=[shadow_x],
            y=[max_val],
            marker_color=country_color,
            opacity=0.7,
            showlegend=False,
            hoverinfo='skip'
        ))

    # Update x-axis: display tick labels only for selected_countries, leaving others blank
    bar_fig.update_xaxes(
        tickmode='array',
        tickvals=x_labels,
        ticktext=[label if label in selected_countries else '' for label in x_labels]
    )
    
    bar_fig.update_layout(
        template='plotly_dark',
        xaxis_title="",
        yaxis_title="",
        yaxis=dict(showticklabels=False),
        xaxis=dict(showticklabels=True),
        barmode='overlay',
        coloraxis_showscale=False,
        showlegend=False,
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return bar_fig



def create_world_map(data, selected_column, selected_date, selected_countries=None):
    """
    Create a Scatter Mapbox using data filtered by the selected date,
    using coordinates from the iso3_coordinates.json file.
    
    Optionally, if selected_iso is provided and found in the JSON file,
    center and zoom the map on that ISO's coordinates.
    """
    # Filter data for the selected date
    filtered_data = data[data['event_date'] == selected_date].copy()
    
    # Load the ISO-3 coordinates from the JSON file
    with open("data/raw/iso3_coordinates.json", "r") as f:
        iso3_coords = json.load(f)
    
    # Add latitude and longitude columns by looking up each ISO_3 code
    filtered_data['lat'] = filtered_data['ISO_3'].apply(lambda iso: iso3_coords.get(iso, [None, None])[0])
    filtered_data['lon'] = filtered_data['ISO_3'].apply(lambda iso: iso3_coords.get(iso, [None, None])[1])
    
    # Create a Scatter Mapbox
    map_fig = px.scatter_mapbox(
        filtered_data,
        lat="lat",
        lon="lon",
        color=selected_column,
        hover_name="country",
        #size=selected_column,  # Optional: size markers by the selected column
        color_continuous_scale=px.colors.sequential.OrRd,
        template='plotly_dark'
    )
    
    # Set map center and zoom level
    # If selected_iso is provided and exists in the coordinates, center on it; otherwise use a default.
    selected_iso = None
    center = {"lat": 20, "lon": 20}  # Default center (world view)
    zoom = 1
    if isinstance(selected_countries, list) and len(selected_countries)==1:
        selected_country = selected_countries[0]
        # Filter the data for the selected country and get the first occurrence of ISO_3
        selected_iso = data.loc[data['country'] == selected_country, 'ISO_3'].iloc[0] if not data.loc[data['country'] == selected_country, 'ISO_3'].empty else None
    if selected_iso and selected_iso in iso3_coords:
        center = {"lat": iso3_coords[selected_iso][0], "lon": iso3_coords[selected_iso][1]}
        zoom = 4  # Adjust zoom level as desired

    # Update layout so the map occupies its container and has no padding
    map_fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0, pad=0),
        autosize=True,
        mapbox=dict(
            style="open-street-map",  # You can change to other Mapbox styles if needed
            center=center,
            zoom=zoom
        ),
        coloraxis_showscale=False
    )
    
    return map_fig


# Callback that calls both functions
@app.callback(
    [Output('bar-plot', 'figure'),
     Output('world-map', 'figure')],
    [Input('frequency', 'value'),
     Input('ranking-column', 'value'),
     Input('ranking-date', 'value'),
     Input('evolution-country', 'value')]
)
def update_bar_and_map(freq, selected_column, selected_date, selected_countries):
    bar_fig = create_bar_plot(freq, selected_column, selected_date, selected_countries)
    map_fig = update_acled_event_map(iso3_data, acled_event_data, selected_column, selected_date, selected_countries)
    #map_fig = create_world_map(data, selected_column, selected_date, selected_countries)
    return bar_fig, map_fig



# Callback for line plot
@app.callback(
    Output('line-plot', 'figure'),
    [Input('frequency', 'value'),
     Input('ranking-column', 'value'),
     Input('evolution-country', 'value'),
     Input('ranking-date', 'value')]
)
def update_line_plot(freq, selected_column, selected_countries, plot_date):
    data = load_all_data(freq)
    # Combine data for selected countries
    combined_data = pd.DataFrame()
    for country in selected_countries:
        country_data = data[data['country'] == country]
        combined_data = pd.concat([combined_data, country_data])
    
    # Define a discrete color mapping for selected countries
    color_sequence = px.colors.qualitative.Plotly
    color_mapping = {country: color_sequence[i % len(color_sequence)] 
                     for i, country in enumerate(selected_countries)}
    
    # Create the line plot using the discrete color mapping
    line_fig = px.line(
        combined_data, 
        x='event_date', 
        y=selected_column, 
        color='country', 
        template='plotly_dark',
        color_discrete_map=color_mapping
    )

    # Compute x-axis range (last 60 dates)
    plot_date
    all_dates = sorted(combined_data[combined_data['event_date']<=plot_date]['event_date'].unique())
    default_range = [all_dates[-60], all_dates[-1]] if len(all_dates) > 60 else [all_dates[0], all_dates[-1]] if all_dates else [plot_date]
    
    line_fig.update_layout(
        xaxis_range=default_range,
        xaxis_title="",
        yaxis_title="",
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation='h', y=-0.3)
    )
    
    # Add scatter markers for each selected country at plot_date
    for country in selected_countries:
        country_data = combined_data[combined_data['country'] == country]
        y_value = 0
        if not country_data.empty and plot_date in country_data['event_date'].values:
            y_value = country_data.loc[country_data['event_date'] == plot_date, selected_column].values[0]
        line_fig.add_scatter(
            x=[plot_date], 
            y=[y_value], 
            mode='markers',
            marker=dict(color='white', size=10, symbol='circle'),
            name=f'{country} date'
        )
    
    # Ensure scatter markers are on top by reordering traces
    line_traces = [trace for trace in line_fig.data if 'lines' in trace.mode]
    scatter_traces = [trace for trace in line_fig.data if 'markers' in trace.mode]
    line_fig.data = tuple(line_traces + scatter_traces)
    
    # Update legend layout
    line_fig.update_layout(showlegend=True)
    
    return line_fig



unavailable_table_cols = ['country', 'month', 'quarter', 'week', 'event_date', 'country', 'ISO_3', 
                          'capital_lat', 'capital_lon', 'violence index_exp_moving_avg', 'General', 
                          'Legislative', 'Local', 'Parliamentary', 'Presidential', 'Referendum', 'holiday']
# Callback for data table
@app.callback(
    [Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('data-table', 'style_data_conditional')],
    [Input('frequency', 'value'),
     Input('ranking-column', 'value'),
     Input('evolution-country', 'value'),
     Input('ranking-date', 'value')]
)
def update_data_table(freq, selected_column, selected_countries, plot_date):
    combined_data = pd.DataFrame()
    data = load_all_data(freq)
    for country in selected_countries:
        country_data = data[data['country'] == country]
        combined_data = pd.concat([combined_data, country_data])

    table_data = []
    for country in selected_countries:
        country_data = combined_data[combined_data['country'] == country]
        # Take the first record where event_date equals plot_date
        latest_values = country_data.loc[country_data['event_date'] == plot_date].to_dict('records')[0]
        table_data.append(latest_values)

    new_table_data = []
    for col in combined_data.columns:
        if col in unavailable_table_cols:
            continue

        string_col = col.replace("_", ": ").replace("/", ", ")
        new_row = {'Country': string_col}
        for i, country in enumerate(selected_countries):
            value = table_data[i][col]
            new_row[country] = np.round(value, 0) if isinstance(value, float) else value

        # Append row if at least one of the countries has a nonzero value
        if any(table_data[i][col] not in [0, '0'] for i in range(len(selected_countries))):
            new_table_data.append(new_row)

    columns = [{'name': 'Country', 'id': 'Country'}] + \
              [{'name': country, 'id': country} for country in selected_countries]

    string_selected_col = selected_column.replace("_", ": ").replace("/", ", ")
    # Create dynamic style: highlight the row where "Country" matches the selected column.
    style_data_conditional = [{
        'if': {
            'filter_query': '{Country} = "' + string_selected_col + '"'
        },
        'color': 'rgb(255, 120, 120)',
        'backgroundColor': 'rgb(60, 50, 50)'
    }]

    return new_table_data, columns, style_data_conditional
