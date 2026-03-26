
import pandas as pd
import sys

def inspect_csv(file_path):
    try:
        df = pd.read_csv(file_path, nrows=0)
        return list(df.columns)
    except Exception as e:
        return [str(e)]

files = {
    "vBillableHoursStaff": "data/vBillableHoursStaff.csv",
    "vwFlatMatters": "data/vwFlatMatters.csv",
    "vMatters": "data/vMatters.csv"
}

with open("csv_info.txt", "w", encoding="utf-8") as f:
    for name, path in files.items():
        f.write(f"--- {name} ---\n")
        cols = inspect_csv(path)
        for col in cols:
            f.write(f"{col}\n")
        f.write("\n")
