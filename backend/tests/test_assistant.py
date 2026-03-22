from fastapi.testclient import TestClient
import pytest
import os
from unittest.mock import patch, MagicMock

# 模拟 OpenAI Client 的响应，因为在 CI/CD 或本地测试中直接调用真实大模型可能不稳定或耗费成本
# 我们在这里使用 unittest.mock 来模拟 get_openai_client 返回的对象
@pytest.fixture
def mock_openai_client():
    with patch("api.assistant.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client

def test_assistant_chat(client: TestClient, auth_headers: dict, mock_openai_client):
    # 配置模拟的返回值
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].message.content = "这是一个关于Python的简单介绍。"
    mock_openai_client.chat.completions.create.return_value = mock_response

    data = {"message": "你好，请给我写一个关于Python的简单介绍。"}
    response = client.post("/api/assistant/", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "这是一个关于Python的简单介绍。"
    assert data["action_taken"] == "chat"

def test_assistant_record_thought(client: TestClient, auth_headers: dict, mock_openai_client):
    # 配置模拟工具调用的返回值
    mock_response = MagicMock()
    mock_message = MagicMock()
    
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "record_thought"
    mock_tool_call.function.arguments = '{"original_content": "明天准备重构一下前台的交互", "tags": "工作"}'
    
    mock_message.tool_calls = [mock_tool_call]
    mock_message.content = "已为您记录想法。"
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = mock_message
    
    mock_openai_client.chat.completions.create.return_value = mock_response

    data = {"message": "帮我记个想法：明天准备重构一下前台的交互，标签设为工作"}
    response = client.post("/api/assistant/", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "记录想法" in data["reply"]
    assert "thought" in data["action_taken"]

def test_assistant_create_schedule(client: TestClient, auth_headers: dict, mock_openai_client):
    # 配置模拟工具调用的返回值
    mock_response = MagicMock()
    mock_message = MagicMock()
    
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "create_schedule"
    mock_tool_call.function.arguments = '{"title": "项目周会", "start_time": "2026-03-24T15:00:00", "location": "A会议室"}'
    
    mock_message.tool_calls = [mock_tool_call]
    mock_message.content = "已为您创建日程。"
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = mock_message
    
    mock_openai_client.chat.completions.create.return_value = mock_response

    data = {"message": "帮我安排个日程：明天下午 3 点在A会议室开项目周会"}
    response = client.post("/api/assistant/", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "创建日程" in data["reply"]
    assert "schedule" in data["action_taken"]
