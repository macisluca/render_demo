import dash_bootstrap_components as dbc

# Navbar layout with dropdown menu for Monitoring
navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Monitoring Events (NEW)", href="/monitoring/eddy"),
                dbc.DropdownMenuItem("Monitoring ACLED", href="/monitoring/acled"),
                dbc.DropdownMenuItem("Monitoring World Bank Data", href="/monitoring/worldbank"),
                dbc.DropdownMenuItem("Monitoring Elections Calendar", href="/monitoring/elections"),
            ],
            nav=True,
            in_navbar=True,
            label="Monitoring",
        ),
        dbc.NavItem(dbc.NavLink("Forecasting", href="/forecasting")),
    ],
    brand="Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
)
