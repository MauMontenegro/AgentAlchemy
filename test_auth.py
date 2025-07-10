import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your API URL

def login(username, password):
    """Attempt to login and get an access token"""
    login_url = f"{BASE_URL}/auth/token"
    
    try:
        response = requests.post(
            login_url,
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"Login successful! User: {token_data['user']['username']}")
            return token_data["access_token"]
        else:
            print(f"Login failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return None

def test_news_agent(token, query="bitcoin", articles=3, mode="simple"):
    """Test the news agent endpoint with authentication"""
    url = f"{BASE_URL}/newsagent/agent"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "query": query,
        "articles": articles,
        "mode": mode
    }
    
    try:
        print(f"Sending request to {url} with token: {token[:10]}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("News agent request successful!")
            result = response.json()
            print(f"Header: {result['header']}")
            print(f"Number of summaries: {len(result['summaries'])}")
            return True
        else:
            print(f"News agent request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error during news agent request: {str(e)}")
        return False

def test_news_agent_without_auth(query="bitcoin", articles=3, mode="simple"):
    """Test the news agent test endpoint without authentication"""
    url = f"{BASE_URL}/newsagent/agent-test"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "articles": articles,
        "mode": mode
    }
    
    try:
        print(f"Sending request to test endpoint {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("News agent test request successful!")
            result = response.json()
            print(f"Header: {result['header']}")
            print(f"Number of summaries: {len(result['summaries'])}")
            return True
        else:
            print(f"News agent test request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error during news agent test request: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_auth.py <username> <password> [query] [articles] [mode]")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    query = sys.argv[3] if len(sys.argv) > 3 else "bitcoin"
    articles = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    mode = sys.argv[5] if len(sys.argv) > 5 else "simple"
    
    print("=== Testing Authentication ===")
    token = login(username, password)
    
    if token:
        print("\n=== Testing News Agent with Authentication ===")
        test_news_agent(token, query, articles, mode)
    
    print("\n=== Testing News Agent without Authentication ===")
    test_news_agent_without_auth(query, articles, mode)