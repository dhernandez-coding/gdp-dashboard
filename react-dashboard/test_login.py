import requests

# Test with admin
data = {'email': 'admin', 'password': 'admin'}
res = requests.post('http://localhost:5000/api/auth/login', json=data)
token = res.json().get('token')
if token:
    headers = {'Authorization': f'Bearer {token}'}
    res2 = requests.get('http://localhost:5000/api/data/revshare', headers=headers)
    print("Admin revshare status:", res2.status_code)
    try:
        print("Admin user_role:", res2.json().get('user_role'))
    except Exception as e:
        print("Error reading user_role", e)

# Test with Russell
data = {'email': 'russell@resolutionlegal.com', 'password': 'admin'}
res = requests.post('http://localhost:5000/api/auth/login', json=data)
token = res.json().get('token')
if token:
    headers = {'Authorization': f'Bearer {token}'}
    res2 = requests.get('http://localhost:5000/api/data/revshare', headers=headers)
    print("Russell user_role:", res2.json().get('user_role'))
