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
        revenue, billable_hours, matters, mtime_key = load_data()
        
        # Add prebills status to the data as well
        try:
            with open(DATA_PATH / "prebills.json", 'r') as f:
                prebills = json.load(f)
        except:
            prebills = {}

        return jsonify({
            'revenue': revenue.to_dict(orient='records'),
            'billable_hours': billable_hours.to_dict(orient='records'),
            'matters': matters.to_dict(orient='records'),
            'prebills': prebills,
            'last_update': mtime_key
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/revenue', methods=['GET'])
@jwt_required()
def get_revenue():
    try:
        revenue, _, _, _ = load_data()
        return jsonify(revenue.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/billable-hours', methods=['GET'])
@jwt_required()
def get_billable_hours():
    try:
        _, billable_hours, _, _ = load_data()
        return jsonify(billable_hours.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/matters', methods=['GET'])
@jwt_required()
def get_matters():
    try:
        _, _, matters, _ = load_data()
        return jsonify(matters.to_dict(orient='records')), 200
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
    """Get all revenue share related data"""
    try:
        revshare, te1, te2, te3 = load_revshare_data()
        if revshare is None:
            return jsonify({'error': 'Could not load revshare data'}), 500
            
        return jsonify({
            'revshare': revshare.to_dict(orient='records'),
            'te_type1': te1.to_dict(orient='records'),
            'te_type2': te2.to_dict(orient='records'),
            'te_type3': te3.to_dict(orient='records')
        }), 200
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
        with open(DATA_PATH / "settings.json", 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({'message': 'Settings saved successfully'}), 200
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
        with open(DATA_PATH / "prebills.json", 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({'message': 'Prebills saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
