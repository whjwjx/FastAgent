from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Generator
import os
from openai import OpenAI
from core.config import settings

router = APIRouter()

class AssistantRequest(BaseModel):
    message: str
    stream: bool = False

class AssistantResponse(BaseModel):
    reply: str

def get_openai_client() -> OpenAI:
    api_key = settings.ARK_API_KEY or os.environ.get("ARK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ARK_API_KEY is not configured")
    
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key
    )

@router.post("/", response_model=AssistantResponse)
def ask_assistant(request: AssistantRequest):
    client = get_openai_client()
    
    try:
        if request.stream:
            # Note: For actual streaming, we should return a StreamingResponse
            # This endpoint is just a fallback for stream=True in a non-streaming endpoint 
            # or we can handle it properly below in another endpoint.
            pass

        completion = client.chat.completions.create(
            model="doubao-1-5-lite-32k-250115",
            messages=[
                {"role": "system", "content": "你是人工智能助手。"},
                {"role": "user", "content": request.message},
            ],
        )
        reply = completion.choices[0].message.content
        return AssistantResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
def ask_assistant_stream(request: AssistantRequest):
    client = get_openai_client()
    
    def generate_stream() -> Generator[str, None, None]:
        try:
            stream = client.chat.completions.create(
                model="doubao-1-5-lite-32k-250115",
                messages=[
                    {"role": "system", "content": "你是人工智能助手。"},
                    {"role": "user", "content": request.message},
                ],
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")
