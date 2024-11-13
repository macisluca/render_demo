import pandas as pd


df = pd.read_csv('/Users/lucamacis/DATA_SCIENCE/Github/Deeplomacy-Forecast/data/external/ACLED_raw.csv')

df['event_date'] = pd.to_datetime(df['event_date'])
df = df[df['event_date']>=pd.to_datetime('2024-10-01')]

df.to_csv('data/last_month_acled.csv', index=False)