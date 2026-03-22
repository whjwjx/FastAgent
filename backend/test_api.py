import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_flow():
    print("Testing Auth...")
    # 1. Register
    reg_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    if r.status_code == 200:
        print("Register Success")
    elif r.status_code == 400 and "already registered" in r.text:
        print("User already exists, proceeding to login")
    else:
        print("Register Failed:", r.text)
        return

    # 2. Login
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    r = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if r.status_code == 200:
        token = r.json()["access_token"]
        print("Login Success, Token obtained")
    else:
        print("Login Failed:", r.text)
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 3. Chat (Idea)
    print("\nTesting Chat (Idea recording)...")
    chat_data = {
        "message": "帮我记录一个想法：关于职场效率的提升方案"
    }
    r = requests.post(f"{BASE_URL}/chat/", json=chat_data, headers=headers)
    if r.status_code == 200:
        print("Chat Idea Response:", r.json()["reply"])
    else:
        print("Chat Idea Failed:", r.text)

    # 4. Get Thoughts
    print("\nTesting Get Thoughts...")
    r = requests.get(f"{BASE_URL}/thoughts/", headers=headers)
    if r.status_code == 200:
        thoughts = r.json()
        print(f"Got {len(thoughts)} thoughts.")
        for t in thoughts:
            print(f"- {t['content']}")
    else:
        print("Get Thoughts Failed:", r.text)

if __name__ == "__main__":
    test_flow()
