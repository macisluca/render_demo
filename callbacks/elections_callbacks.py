from dash.dependencies import Input, Output
from dash import html, dash_table
from app_instance import app
from utils.data_loader import load_electoral_data

elections_df = load_electoral_data()

# Callback to generate tables
@app.callback(
    Output('tables-container', 'children'),
    Input('year-dropdown', 'value')
)
def update_tables(selected_year):
    if selected_year is None:
        return html.Div("Please select a year.")

    # Filter elections for the selected year
    year_df = elections_df[elections_df['year'] == selected_year].copy()
    # Format the 'date' column and sort by date
    year_df['formatted_date'] = year_df['date'].dt.strftime('%d %B')
    # Change 31 december to "to be scheduled"
    year_df['formatted_date'] = year_df['date'].apply(
    lambda x: "to be scheduled" if x.strftime('%d %B') == '31 December' else x.strftime('%d %B'))
    year_df = year_df.sort_values(by='date')

    # Prepare a table for each month
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    tables = []
    for month in months:
        # Filter elections for this month
        month_df = year_df[year_df['month'] == month][['formatted_date', 'title']]

        if not month_df.empty:
            # Create a table with election data
            table = dash_table.DataTable(
                columns=[
                    {"name": "Date", "id": "formatted_date"},
                    {"name": "Election Title", "id": "title"}
                ],
                data=month_df.to_dict('records'),
                style_table={'width': '100%'},
                style_data={'color': 'white','backgroundColor': 'rgb(50, 50, 50)'},
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
                style_cell={'textAlign': 'left', 'height': 'auto', 'minWidth': '90px', 'width': '180px', 'maxWidth': '180px', 'whiteSpace': 'normal'},

            )
        else:
            # No elections for this month
            table = html.Div("No elections", style={'color': 'gray', 'fontStyle': 'italic'})

        # Add a header and table to the layout
        tables.append(html.Div([
            html.H3(month),
            table,
            html.Hr(style={'borderTop': '1px solid black'})
        ]))

    return tables
