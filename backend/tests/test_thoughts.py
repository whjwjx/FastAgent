from fastapi.testclient import TestClient

def test_create_and_get_thoughts(client: TestClient, auth_headers: dict):
    # 1. Create Thought
    thought_data = {
        "original_content": "测试直接调用接口创建的想法",
        "tags": ["API测试"],
        "thought_type": "idea"
    }
    response = client.post("/api/thoughts/", json=thought_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["original_content"] == "测试直接调用接口创建的想法"
    assert data["thought_type"] == "idea"
    assert "id" in data

    # 1.1 Create Blog Thought
    blog_data = {
        "original_content": "# 这是一篇测试博客",
        "thought_type": "blog",
        "source_ids": ["1", "2"]
    }
    response = client.post("/api/thoughts/", json=blog_data, headers=auth_headers)
    assert response.status_code == 200
    blog_resp = response.json()
    assert blog_resp["thought_type"] == "blog"
    assert blog_resp["source_ids"] == ["1", "2"]

    # 2. Get Thoughts
    response = client.get("/api/thoughts/", headers=auth_headers)
    assert response.status_code == 200
    thoughts = response.json()
    assert len(thoughts) >= 2

    # 3. Get specific type thoughts
    response = client.get("/api/thoughts/?thought_type=blog", headers=auth_headers)
    assert response.status_code == 200
    blog_thoughts = response.json()
    assert len(blog_thoughts) == 1
    assert blog_thoughts[0]["thought_type"] == "blog"
