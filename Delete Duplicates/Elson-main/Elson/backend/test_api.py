import requests
import sys

def test_api():
    try:
        url_base = 'http://127.0.0.1:8888'
        
        # Try to access the test endpoint
        response = requests.get(f'{url_base}/api/v1/test')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.json()}")
        
        # Try to access the system-info endpoint
        response = requests.get(f'{url_base}/api/v1/system-info')
        print(f"System Info Response status: {response.status_code}")
        print(f"System Info Response content: {response.json()}")
        
        # Try to access the db-test endpoint
        response = requests.get(f'{url_base}/api/v1/db-test')
        print(f"DB Test Response status: {response.status_code}")
        print(f"DB Test Response content: {response.json()}")
        
        # Try to access the health endpoint
        response = requests.get(f'{url_base}/health')
        print(f"Health Response status: {response.status_code}")
        print(f"Health Response content: {response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    test_api()