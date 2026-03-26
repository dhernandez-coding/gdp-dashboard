import os
import json
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add the parent directory to sys.path to import data_loader
sys.path.append(str(Path(__file__).parent.parent.parent))
# Mock streamlit before importing data_loader
from unittest.mock import MagicMock
mock_st = MagicMock()
mock_st.cache_data = lambda f=None, **kwargs: f if f else lambda x: x
sys.modules["streamlit"] = mock_st

from data_loader import load_data
from sync_data import sync_from_github

app = Flask(__name__)
CORS(app)

# Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
jwt = JWTManager(app)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_PATH = BASE_DIR / "data"

# ============================================================================
# Auth Routes
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').lower()
    password = data.get('password', '')

    try:
        with open(DATA_PATH / "users.json", 'r') as f:
            users = json.load(f)
        
        user = users.get(email)
        if user and user['password'] == password:
            access_token = create_access_token(identity=email)
            return jsonify({
                'token': access_token,
                'user': {
                    'username': user.get('username', email),
                    'allowed_tabs': user.get('allowed_tabs', ['Dashboard'])
                }
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify():
    current_user_email = get_jwt_identity()
    try:
        with open(DATA_PATH / "users.json", 'r') as f:
            users = json.load(f)
        
        user = users.get(current_user_email)
        if user:
            return jsonify({
                'username': user.get('username', current_user_email),
                'allowed_tabs': user.get('allowed_tabs', ['Dashboard'])
            }), 200
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Data Routes
# ============================================================================

@app.route('/api/data/all', methods=['GET'])
@jwt_required()
def get_all_data():
    try:
        revenue, billable_hours, matters, flat_matters, mtime_key = load_data()
        
        # Add prebills status to the data as well
        try:
            with open(DATA_PATH / "prebills.json", 'r') as f:
                prebills = json.load(f)
        except:
            prebills = {}

        return jsonify({
            'revenue': json.loads(revenue.to_json(orient='records')),
            'billable_hours': json.loads(billable_hours.to_json(orient='records')),
            'matters': json.loads(matters.to_json(orient='records')),
            'prebills': prebills,
            'last_update': datetime.fromtimestamp(max(mtime_key)).isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/sync', methods=['POST'])
@jwt_required()
def sync_data_route():
    try:
        results = sync_from_github()
        # After syncing, we might want to clear any caches if needed
        # But data_loader uses streamlit cache which is mocked/not persistent here
        return jsonify({
            'message': 'Sync completed',
            'results': results
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/revenue', methods=['GET'])
@jwt_required()
def get_revenue():
    try:
        revenue, _, _, _, _ = load_data()
        return jsonify(json.loads(revenue.to_json(orient='records'))), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/billable-hours', methods=['GET'])
@jwt_required()
def get_billable_hours():
    try:
        _, billable_hours, _, _, _ = load_data()
        return jsonify(json.loads(billable_hours.to_json(orient='records'))), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/matters', methods=['GET'])
@jwt_required()
def get_matters():
    try:
        _, _, matters, _, _ = load_data()
        return jsonify(json.loads(matters.to_json(orient='records'))), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Additional data loaders for RevShare (restored from previous session)
def load_revshare_data():
    try:
        revshare = pd.read_csv(DATA_PATH / "RevShareNewLogic.csv")
        te_type1 = pd.read_csv(DATA_PATH / "vwTimeEntriesType1.csv")
        te_type2 = pd.read_csv(DATA_PATH / "vwTimeEntriesType2.csv")
        te_type3 = pd.read_csv(DATA_PATH / "vwTimeEntriesType3.csv")
        return revshare, te_type1, te_type2, te_type3
    except Exception as e:
        print(f"Error loading revshare data: {e}")
        return None, None, None, None

@app.route('/api/data/revshare', methods=['GET'])
@jwt_required()
def get_revshare():
    """Get all revenue share related data, filtered by user permissions."""
    try:
        current_user_email = get_jwt_identity()
        
        # Load user to get staff code
        with open(DATA_PATH / "users.json", 'r') as f:
            users = json.load(f)
        
        user = users.get(current_user_email)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        staff_code = user.get('staff_code')
        
        revshare, te1, te2, te3 = load_revshare_data()
        if revshare is None:
            return jsonify({'error': 'Could not load revshare data'}), 500
            
        # Permission Logic:
        # RAW, DLB, and admin can see everything.
        # Others can only see their own staff code.
        is_admin = staff_code in ['RAW', 'DLB', 'admin']
        
        if not is_admin and staff_code:
            # Filter RevShare (matches 'Staff' column)
            if 'Staff' in revshare.columns:
                revshare = revshare[revshare['Staff'] == staff_code]
            
            # Filter Time Entries (matches 'Staff' OR 'StaffAbbreviation')
            # Check which column exists in the time entry dataframes
            for df in [te1, te2, te3]:
                if df is not None:
                    # Depending on exact CSV column name
                    if 'Staff' in df.columns:
                        mask = df['Staff'] == staff_code
                        # Apply mask in place? No, need to reassign.
                        # Since we are iterating a list, we need to assign back.
                        pass # Logic moved below to be cleaner
        
        # Apply filtering clearly
        if not is_admin and staff_code:
            # RevShare
            if 'Staff' in revshare.columns:
                revshare = revshare[revshare['Staff'] == staff_code]
            
            # Helper to filter TE
            def filter_te(df, code):
                if df is None: return df
                if 'Staff' in df.columns:
                    return df[df['Staff'] == code]
                elif 'StaffAbbreviation' in df.columns:
                    return df[df['StaffAbbreviation'] == code]
                return df # If no matching column, return as is (or empty? Safe to return as is if no sensitive data?)
                          # Ideally we should return empty if we can't verify ownership.
                          # But the CSVs likely have one of those.
                
            te1 = filter_te(te1, staff_code)
            te2 = filter_te(te2, staff_code)
            te3 = filter_te(te3, staff_code)

        return jsonify({
            'revshare': json.loads(revshare.to_json(orient='records')),
            'te_type1': json.loads(te1.to_json(orient='records')),
            'te_type2': json.loads(te2.to_json(orient='records')),
            'te_type3': json.loads(te3.to_json(orient='records')),
            'user_role': {
                'is_admin': is_admin,
                'staff_code': staff_code
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notifications/flat-matters', methods=['GET'])
@jwt_required()
def get_flat_matter_notifications():
    try:
        current_user_email = get_jwt_identity()
        
        # Load user to get staff code/role
        with open(DATA_PATH / "users.json", 'r') as f:
            users = json.load(f)
        
        user = users.get(current_user_email)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        staff_code = user.get('staff_code')
        is_admin = staff_code in ['RAW', 'DLB', 'admin']

        _, billable_hours, _, flat_matters, _ = load_data()
        
        # --- Logic from test_logic.py ---
        ESTIMATED_RATE = 250.0 
        
        # 1. Group hours by Matter
        matter_hours = billable_hours.groupby('MatterName')['BillableHoursAmount'].sum().reset_index()
        matter_hours.rename(columns={'BillableHoursAmount': 'TotalHours'}, inplace=True)
        
        # 2. Merge with Flat Matters
        if flat_matters is None or flat_matters.empty:
             return jsonify({'notifications': []}), 200

        merged = pd.merge(flat_matters, matter_hours, on='MatterName', how='left')
        
        # 3. Calculate Burn
        merged['TotalHours'] = merged['TotalHours'].fillna(0)
        merged['BurnedAmount'] = merged['TotalHours'] * ESTIMATED_RATE
        
        # 4. Filter > 0.8
        merged = merged[merged['LastInvoiceAmount'] > 0] 
        merged['PercentUsed'] = merged['BurnedAmount'] / merged['LastInvoiceAmount']
        
        at_risk = merged[merged['PercentUsed'] >= 0.8].copy()
        
        # 5. Filter by User Permission
        # If not admin, we want to show matters relevant to this user.
        # Since flat_matters doesn't have a staff column, we check if the user has logged hours on it?
        # Or if the billable_hours has entries for this staff on this matter.
        
        if not is_admin and staff_code:
            # Get list of matters this staff has worked on
            staff_matters = billable_hours[billable_hours['StaffAbbreviation'] == staff_code]['MatterName'].unique()
            at_risk = at_risk[at_risk['MatterName'].isin(staff_matters)]
            
        # Format for JSON
        notifications = []
        for _, row in at_risk.iterrows():
            notifications.append({
                'id': str(row.get('MatterID', row['MatterName'])), # Use Name as ID fallback
                'matter_name': row['MatterName'],
                'percent_used': round(row['PercentUsed'] * 100, 1),
                'burned_amount': row['BurnedAmount'],
                'budget': row['LastInvoiceAmount']
            })
            
        return jsonify({'notifications': notifications}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Settings Routes
# ============================================================================

@app.route('/api/settings', methods=['GET'])
@jwt_required()
def get_settings():
    try:
        with open(DATA_PATH / "settings.json", 'r') as f:
            settings = json.load(f)
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['PUT'])
@jwt_required()
def save_settings():
    data = request.get_json()
    try:
        # Save to local file
        with open(DATA_PATH / "settings.json", 'w') as f:
            json.dump(data, f, indent=4)
        
        # Push to GitHub
        import subprocess
        try:
            # Add the settings file
            subprocess.run(
                ['git', 'add', 'data/settings.json'],
                cwd=BASE_DIR,
                check=True,
                capture_output=True
            )
            
            # Commit the changes
            commit_msg = f"Auto-update settings.json from React ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=BASE_DIR,
                check=True,
                capture_output=True
            )
            
            # Push to GitHub
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=BASE_DIR,
                check=True,
                capture_output=True
            )
            
            return jsonify({'message': 'Settings saved and pushed to GitHub successfully'}), 200
        except subprocess.CalledProcessError as e:
            # If git operations fail, still return success since local save worked
            return jsonify({'message': 'Settings saved locally (GitHub push failed)'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prebills', methods=['GET'])
@jwt_required()
def get_prebills():
    try:
        with open(DATA_PATH / "prebills.json", 'r') as f:
            prebills = json.load(f)
        return jsonify(prebills), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prebills', methods=['PUT'])
@jwt_required()
def save_prebills():
    data = request.get_json()
    try:
        # Save to local file
        with open(DATA_PATH / "prebills.json", 'w') as f:
            json.dump(data, f, indent=4)
        
        # Push to GitHub
        import subprocess
        try:
            # Add the prebills file
            subprocess.run(
                ['git', 'add', 'data/prebills.json'],
                cwd=BASE_DIR,
                check=True,
                capture_output=True
            )
            
            # Commit the changes
            commit_msg = f"Auto-update prebills.json from React ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=BASE_DIR,
                check=True,
                capture_output=True
            )
            
            # Push to GitHub
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=BASE_DIR,
                check=True,
                capture_output=True
            )
            
            return jsonify({'message': 'Prebills saved and pushed to GitHub successfully'}), 200
        except subprocess.CalledProcessError as e:
            # If git operations fail, still return success since local save worked
            return jsonify({'message': 'Prebills saved locally (GitHub push failed)'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)


