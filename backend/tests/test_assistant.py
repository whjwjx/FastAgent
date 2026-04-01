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
    def mock_create_generator(*args, **kwargs):
        if kwargs.get('stream') is False:
            mock_resp = MagicMock()
            mock_message = MagicMock()
            mock_message.tool_calls = None
            mock_message.content = "这是一个关于Python的简单介绍。"
            mock_message.model_dump.return_value = {"role": "assistant", "content": "这是一个关于Python的简单介绍。"}
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message = mock_message
            return mock_resp
            
        mock_stream_resp = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "这是一个关于Python的简单介绍。"
        return [mock_chunk]
        
    mock_openai_client.chat.completions.create.side_effect = mock_create_generator

    data = {"message": "你好，请给我写一个关于Python的简单介绍。"}
    response = client.post("/api/assistant/stream", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "这是一个关于Python的简单介绍" in content

def test_assistant_record_thought(client: TestClient, auth_headers: dict, mock_openai_client):
    def mock_create_generator(*args, **kwargs):
        # 针对第一轮调用的 mock
        if kwargs.get('stream') is False:
            mock_resp = MagicMock()
            mock_message = MagicMock()
            
            mock_tool_call = MagicMock()
            mock_tool_call.function.name = "thought:crud:create"
            mock_tool_call.function.arguments = '{"original_content": "明天准备重构一下前台的交互", "tags": "工作"}'
            
            mock_message.tool_calls = [mock_tool_call]
            mock_message.model_dump.return_value = {"role": "assistant", "tool_calls": [{"function": {"name": "thought:crud:create", "arguments": '{"original_content": "明天准备重构一下前台的交互", "tags": "工作"}'}}]}
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message = mock_message
            return mock_resp
            
        # 针对第二轮流式调用的 mock
        mock_stream_resp = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "已为您记录想法。"
        return [mock_chunk]
        
    mock_openai_client.chat.completions.create.side_effect = mock_create_generator

    data = {"message": "帮我记个想法：明天准备重构一下前台的交互，标签设为工作"}
    response = client.post("/api/assistant/stream", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "已为您记录想法" in content

def test_assistant_create_schedule(client: TestClient, auth_headers: dict, mock_openai_client):
    def mock_create_generator(*args, **kwargs):
        if kwargs.get('stream') is False:
            mock_resp = MagicMock()
            mock_message = MagicMock()
            
            mock_tool_call = MagicMock()
            mock_tool_call.function.name = "schedule:crud:create"
            mock_tool_call.function.arguments = '{"title": "项目周会", "start_time": "2026-03-24T15:00:00", "location": "A会议室"}'
            
            mock_message.tool_calls = [mock_tool_call]
            mock_message.model_dump.return_value = {"role": "assistant", "tool_calls": [{"function": {"name": "schedule:crud:create", "arguments": '{"title": "项目周会", "start_time": "2026-03-24T15:00:00", "location": "A会议室"}'}}]}
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message = mock_message
            return mock_resp
            
        mock_stream_resp = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "已为您创建日程。"
        return [mock_chunk]
        
    mock_openai_client.chat.completions.create.side_effect = mock_create_generator

    data = {"message": "帮我安排个日程：明天下午 3 点在A会议室开项目周会"}
    response = client.post("/api/assistant/stream", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "已为您创建日程" in content
