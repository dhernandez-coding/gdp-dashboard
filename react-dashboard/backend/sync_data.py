import os
import requests
from pathlib import Path

# Repository details
REPO = "dhernandez-coding/gdp-dashboard"
BRANCH = "main"
DATA_FILES = [
    "RevShareNewLogic.csv",
    "vBillableHoursStaff.csv",
    "vMatters.csv",
    "vwFlatMatters.csv",
    "vTimeEntries.csv",
    "vwTimeEntriesType1.csv",
    "vwTimeEntriesType2.csv",
    "vwTimeEntriesType3.csv",
    "StaffGoalsSettings.csv",
    "users.json"
]

def sync_from_github():
    """Download the latest data files from GitHub."""
    token = os.environ.get("GITHUB_TOKEN")
    base_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/data"
    
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    # Path to the data folder relative to this script
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for filename in DATA_FILES:
        url = f"{base_url}/{filename}"
        print(f"Downloading {filename}...")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            with open(data_dir / filename, "wb") as f:
                f.write(response.content)
            results.append({"file": filename, "status": "success"})
        else:
            results.append({
                "file": filename, 
                "status": "failed", 
                "error": f"HTTP {response.status_code}"
            })
            
    return results

if __name__ == "__main__":
    # Test run
    sync_results = sync_from_github()
    for res in sync_results:
        print(f"{res['file']}: {res['status']}")
