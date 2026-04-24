# Create empty_forebet.py
import pandas as pd
from datetime import date
import os

csv_files_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'CSV FILES/{date.today()} Files')
os.makedirs(csv_files_path, exist_ok=True)

columns = ['DATE', 'TIME', 'HOME TEAM', 'AWAY TEAM', 'HOME PER', 'DRAW PER', 
           'AWAY PER', 'UNDER 2.5', 'OVER 2.5', 'BTS', 'OTS', 'NAME']

filepath = os.path.join(csv_files_path, 'forebet.csv')
pd.DataFrame(columns=columns).to_csv(filepath, index=False)
print(f"Created empty forebet.csv at {filepath}")
