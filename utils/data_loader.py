import os
import pandas as pd

DATA_PATH = 'data/interim/data_ready/'
FORECAST_PATH = 'models/TiDE/predictions/'
ISO3_PATH = 'data/raw/ACLED_coverage_ISO3.csv'

def load_all_data():
    files = [f for f in os.listdir(DATA_PATH) if f.endswith('.csv')]
    dfs = [pd.read_csv(os.path.join(DATA_PATH, file)) for file in files]
    return pd.concat(dfs, ignore_index=True)

def load_forecast_data(variable, window):
    folder_path = os.path.join(FORECAST_PATH, variable, window)
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    dfs = [pd.read_csv(os.path.join(folder_path, file)) for file in files]
    return pd.concat(dfs, ignore_index=True)

def load_crisis_data(variable, window):
    crisis_report_path = f'reports/tables/operative/TiDE/{variable}/{window}'
    files = [f for f in os.listdir(crisis_report_path) if f.endswith('.csv')]
    dfs = [pd.read_csv(os.path.join(crisis_report_path, file)) for file in files]
    return pd.concat(dfs, ignore_index=True)

def load_electoral_data():
    # Load elections data
    elections_df = pd.read_csv("data/elections_calendar.csv")
    # Convert '_begin' to datetime, and ensure that invalid values are coerced to NaT (Not a Time)
    elections_df['_begin'] = pd.to_datetime(elections_df['_begin'], errors='coerce', utc=True)
    # Now create the 'date' column as a datetime.date object (if not already done)
    elections_df['date'] = pd.to_datetime(elections_df['_begin'].dt.date)
    elections_df['year'] = elections_df['_begin'].dt.year
    elections_df['month'] = elections_df['_begin'].dt.month_name()
    # Sort by date
    elections_df = elections_df.sort_values(by='date', ascending=False)
    return elections_df

def load_ISO3_data():
    return pd.read_csv(ISO3_PATH)

def load_event_data():
    df = pd.read_csv('data/eddy.csv')
    df = df.dropna(subset=["latitude", "longitude"], how="all")
    df["event_date"] = pd.to_datetime(df["date_publish"]).dt.date
    df = df.dropna(subset=["event_date"])
    return df

def load_ACLED_event_data(acled_path='data/last_month_acled.csv'):
    return pd.read_csv(acled_path)


def load_WDI_data(directory_wdi = "data/WDI/"):
    # List all CSV files in the directory
    csv_files = [os.path.join(directory_wdi, file) for file in os.listdir(directory_wdi) if file.endswith('.csv')]
    # Concatenate all CSV files into a single DataFrame
    wdi_raw_df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)
    acled_coverage_iso3_df = pd.read_csv("data/raw/ACLED_coverage_ISO3.csv")
    # Merge to add the "Country" column
    wdi_df = pd.merge(
        wdi_raw_df,
        acled_coverage_iso3_df[['ISO_3166-3', 'Country']],
        how='left',
        left_on='ISO_3',
        right_on='ISO_3166-3'
    )
    return wdi_df
