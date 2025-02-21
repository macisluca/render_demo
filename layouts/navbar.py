import dash_bootstrap_components as dbc

# Navbar layout with dropdown menu for Monitoring
navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Monitoring EDDY Events", href="/monitoring/eddy"),
                dbc.DropdownMenuItem("Monitoring ACLED", href="/monitoring/acled"),
                dbc.DropdownMenuItem("Monitoring World Bank Data", href="/monitoring/worldbank"),
                dbc.DropdownMenuItem("Monitoring Elections Calendar", href="/monitoring/elections"),
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
    brand="Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
)
