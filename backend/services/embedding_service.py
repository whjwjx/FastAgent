from typing import List, Optional
import httpx
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_embedding(text: str) -> Optional[List[float]]:
    """
    调用火山引擎 (Volcengine) 多模态 Embedding API 获取文本向量。
    支持可选配置：如果未配置 API Key 或模型，将跳过向量生成。
    """
    if not text or not text.strip():
        logger.warning("Attempted to get embedding for empty text.")
        return None
        
    # --- 可选性检查 ---
    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your-api-key-here":
        logger.info("Skipping embedding generation: LLM_API_KEY is not configured.")
        return None
    
    if not settings.LLM_BASE_URL:
        logger.info("Skipping embedding generation: LLM_BASE_URL is not configured.")
        return None
    
    if not settings.EMBEDDING_MODEL:
        logger.info("Skipping embedding generation: EMBEDDING_MODEL is not configured.")
        return None
    # ----------------
        
    logger.info(f"Generating embedding using model: {settings.EMBEDDING_MODEL}")
    logger.info(f"Input text (first 50 chars): {text[:50]}...")
        
    try:
        # 豆包多模态向量模型通常是 1024 或 2048 维，请确保数据库中的 vector(1536) 与之匹配。
        # 如果模型返回维度不匹配，需要修改 models.py 中的 Vector(维度)
        url = f"{settings.LLM_BASE_URL}/embeddings/multimodal"
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
        
        with httpx.Client(timeout=30.0) as client:
            logger.info(f"Sending POST request to {url}")
            response = client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Embedding API failed with status {response.status_code}: {response.text}")
                response.raise_for_status()
                
            data = response.json()
            
            # 提取向量结果
            # 注意：多模态接口返回的 data 可能是字典也可能是列表
            result_data = data.get("data")
            if not result_data:
                logger.error(f"Unexpected response format from Volcengine (missing 'data'): {data}")
                return None
                
            embedding = None
            if isinstance(result_data, list):
                if len(result_data) > 0 and "embedding" in result_data[0]:
                    embedding = result_data[0]["embedding"]
                else:
                    logger.error(f"Response data list is empty or missing 'embedding': {result_data}")
            elif isinstance(result_data, dict):
                if "embedding" in result_data:
                    embedding = result_data["embedding"]
                else:
                    logger.error(f"Response data dict missing 'embedding': {result_data}")
            else:
                logger.error(f"Unexpected type for 'data' field: {type(result_data)}")

            if embedding:
                logger.info(f"Successfully generated embedding. Dimension: {len(embedding)}")
                return embedding
            else:
                return None
                
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None
