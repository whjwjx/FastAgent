from fastapi.testclient import TestClient

def test_create_and_get_thoughts(client: TestClient, auth_headers: dict):
    # 1. Create Thought
    thought_data = {
        "original_content": "测试直接调用接口创建的想法",
        "tags": "API测试"
    }
    response = client.post("/api/thoughts/", json=thought_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["original_content"] == "测试直接调用接口创建的想法"
    assert "id" in data

    # 2. Get Thoughts
    response = client.get("/api/thoughts/", headers=auth_headers)
    assert response.status_code == 200
    thoughts = response.json()
    assert len(thoughts) > 0
    assert thoughts[0]["original_content"] == "测试直接调用接口创建的想法"
