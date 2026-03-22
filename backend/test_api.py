import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def test_flow():
    print("================ 1. Testing Auth ================")
    # 1. Register
    reg_data = {
        "username": "testuser_mvp",
        "email": "test_mvp@example.com",
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
        "username": "testuser_mvp",
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

    print("\n================ 2. Testing Thoughts API ================")
    # Create Thought
    thought_data = {
        "original_content": "测试直接调用接口创建的想法",
        "tags": "API测试"
    }
    r = requests.post(f"{BASE_URL}/thoughts/", json=thought_data, headers=headers)
    if r.status_code == 200:
        print("Create Thought Success:", r.json()["original_content"])
    else:
        print("Create Thought Failed:", r.text)

    # Get Thoughts
    r = requests.get(f"{BASE_URL}/thoughts/", headers=headers)
    if r.status_code == 200:
        print(f"Get Thoughts Success: Found {len(r.json())} thoughts.")
    else:
        print("Get Thoughts Failed:", r.text)


    print("\n================ 3. Testing Schedules API ================")
    # Create Schedule
    start_time = (datetime.now() + timedelta(days=1)).isoformat()
    schedule_data = {
        "title": "测试接口直接创建的日程",
        "start_time": start_time,
        "location": "虚拟会议室"
    }
    r = requests.post(f"{BASE_URL}/schedules/", json=schedule_data, headers=headers)
    if r.status_code == 200:
        print("Create Schedule Success:", r.json()["title"])
    else:
        print("Create Schedule Failed:", r.text)

    # Get Schedules
    r = requests.get(f"{BASE_URL}/schedules/", headers=headers)
    if r.status_code == 200:
        print(f"Get Schedules Success: Found {len(r.json())} schedules.")
    else:
        print("Get Schedules Failed:", r.text)


    print("\n================ 4. Testing AI Assistant (Agent Router) ================")
    print("--> 4.1 Testing Chat Thought")
    chat_thought_data = {
        "message": "帮我记个想法：明天准备重构一下前台的交互，标签设为工作"
    }
    r = requests.post(f"{BASE_URL}/assistant/", json=chat_thought_data, headers=headers)
    if r.status_code == 200:
        print("Agent Thought Response:")
        print(r.json()["reply"])
    else:
        print("Agent Thought Failed:", r.text)

    print("\n--> 4.2 Testing Chat Schedule")
    chat_schedule_data = {
        "message": "帮我安排个日程：明天下午 3 点在A会议室开项目周会"
    }
    r = requests.post(f"{BASE_URL}/assistant/", json=chat_schedule_data, headers=headers)
    if r.status_code == 200:
        print("Agent Schedule Response:")
        print(r.json()["reply"])
    else:
        print("Agent Schedule Failed:", r.text)

    print("\n================ 5. Verifying AI Actions ================")
    r = requests.get(f"{BASE_URL}/thoughts/", headers=headers)
    if r.status_code == 200:
        thoughts = r.json()
        print(f"Thoughts count now: {len(thoughts)}")
        if thoughts:
            print(f"Latest Thought: {thoughts[0].get('original_content')}")

    r = requests.get(f"{BASE_URL}/schedules/", headers=headers)
    if r.status_code == 200:
        schedules = r.json()
        print(f"Schedules count now: {len(schedules)}")
        if schedules:
            print(f"Latest Schedule: {schedules[-1].get('title')} at {schedules[-1].get('start_time')}")

if __name__ == "__main__":
    test_flow()
