import dash_bootstrap_components as dbc

# Navbar layout with dropdown menu for Monitoring
navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Explore Events", href="/monitoring/acled"),
                dbc.DropdownMenuItem("Explore Socio-Political Data", href="/monitoring/worldbank"),
                dbc.DropdownMenuItem("Explore Elections", href="/monitoring/elections"),
                #dbc.DropdownMenuItem("Explore EDDY Events (Just a Sample)", href="/monitoring/eddy"),
            ],
            align_end=True,
            nav=True,
            in_navbar=True,
            label="Monitoring",
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Forecasting Global", href="/forecasting/global"),
                dbc.DropdownMenuItem("Forecasting per Country", href="/forecasting/country"),
            ],
            align_end=True,
            nav=True,
            in_navbar=True,
            label="Forecasting",
        ),
    ],
    brand="Deeplomacy",
    brand_href="/",
    color="primary",
    dark=True,
    style={
        'padding-top': '0.2rem',
        'padding-bottom': '0.2rem',
        'padding-left': '1rem',
        'padding-right': '1rem'
    }
)
