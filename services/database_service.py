import requests
import os

class DatabaseService:
    def __init__(self):
        self.api_url = os.getenv('DATABASE_API_URL', 'http://localhost:8000')
    
    def request(self, method, endpoint, data=None, token=None):
        try:
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            
            if method.upper() == 'GET':
                response = requests.get(f"{self.api_url}{endpoint}", headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(f"{self.api_url}{endpoint}", json=data, headers=headers)
            else:
                return None
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Database API error: {e}")
            return None
    
    def login_user(self, identifier, password):
        return self.request('POST', '/api/login', {
            'identifier': identifier,
            'password': password
        })
    
    def register_user(self, username, email, password):
        return self.request('POST', '/api/users', {
            'username': username,
            'email': email,
            'password': password,
            'role': 'user'
        })
    
    def check_session(self, token):
        return self.request('GET', '/api/check-session', token=token)
    
    def get_users(self, token):
        return self.request('GET', '/api/admin/users', token=token)
    
    def get_concerts(self, token):
        return self.request('GET', '/api/concerts', token=token)
    
    def get_admin_stats(self, token):
        return self.request('GET', '/api/admin/stats', token=token)