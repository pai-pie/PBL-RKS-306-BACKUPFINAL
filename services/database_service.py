import requests
import os

class DatabaseService:
    def __init__(self, security_service=None):
        self.api_url = os.getenv('DATABASE_API_URL', 'http://localhost:8000')
        self.security = security_service
    
    def request(self, method, endpoint, data=None, token=None):
        try:
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            
            # Sanitize data jika security_service available
            if data and self.security:
                sanitized_data = {}
                for key, value in data.items():
                    if isinstance(value, str) and key != 'password':
                        sanitized_data[key] = self.security.sanitize_input(value)
                    else:
                        sanitized_data[key] = value
                data = sanitized_data
            
            url = f"{self.api_url}{endpoint}"
            print(f"🔗 API CALL: {method} {url}")  # Debug log
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                return None
                
            print(f"📡 RESPONSE: {response.status_code}")  # Debug log
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Database API error: {e}")
            return None
    
    def get_user_by_email(self, email, token=None):
        """Get user by email untuk login verification"""
        if self.security:
            email = self.security.sanitize_input(email)
        response = self.request('GET', f'/api/users?email={email}', token=token)
        
        # Debug: Print response untuk troubleshooting
        if response:
            print(f"👤 User data response: {response.status_code}")
            try:
                print(f"📄 Response content: {response.json()}")
            except:
                print("📄 Response content: Unable to parse JSON")
        
        return response
    
    def login_user(self, identifier, password):
        return self.request('POST', '/api/login', {
            'identifier': identifier,
            'password': password
        })
    
    def register_user(self, user_data):
        return self.request('POST', '/api/users', user_data)
    
    def check_session(self, token):
        return self.request('GET', '/api/check-session', token=token)
    
    def get_users(self, token):
        return self.request('GET', '/api/admin/users', token=token)
    
    def get_concerts(self, token):
        return self.request('GET', '/api/concerts', token=token)
    
    def get_admin_stats(self, token):
        return self.request('GET', '/api/admin/stats', token=token)