from fastapi.testclient import TestClient
from datetime import datetime, timedelta

def test_create_and_get_schedules(client: TestClient, auth_headers: dict):
    # 1. Create Schedule
    start_time = (datetime.now() + timedelta(days=1)).isoformat()
    schedule_data = {
        "title": "测试接口直接创建的日程",
        "start_time": start_time,
        "location": "虚拟会议室"
    }
    response = client.post("/api/schedules/", json=schedule_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "测试接口直接创建的日程"
    assert "id" in data

    # 2. Get Schedules
    response = client.get("/api/schedules/", headers=auth_headers)
    assert response.status_code == 200
    schedules = response.json()
    assert len(schedules) > 0
    assert schedules[0]["title"] == "测试接口直接创建的日程"
