import requests

# Test user creation
api_url = "http://auth361.vercel.app/create"
data = {"username": "testing", "password": "test"}
response = requests.post(api_url, json=data)
print(f"Create Response: {response.status_code}, {response.text}")

# Test user authentication
api_url = "http://auth361.vercel.app/auth"
data = {"username": "username1", "password": "password123"}
response = requests.post(api_url, json=data)
print(f"Auth Response: {response.status_code}, {response.text}")

