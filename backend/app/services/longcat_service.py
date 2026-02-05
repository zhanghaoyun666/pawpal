"""
美团 LongCat 大模型服务
文档参考: https://ai.meituan.com/docs
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LongCat API 配置
LONGCAT_API_KEY = os.getenv("LONGCAT_API_KEY")
LONGCAT_SECRET_KEY = os.getenv("LONGCAT_SECRET_KEY")  # 部分接口需要
LONGCAT_BASE_URL = os.getenv("LONGCAT_BASE_URL", "https://api.longcat.chat/openai")
LONGCAT_MODEL = os.getenv("LONGCAT_MODEL", "LongCat-Flash-Thinking")  # 或其他可用模型


class LongCatService:
    """美团 LongCat AI 服务"""
    
    def __init__(self):
        self.api_key = LONGCAT_API_KEY
        self.secret_key = LONGCAT_SECRET_KEY
        self.base_url = LONGCAT_BASE_URL
        self.model = LONGCAT_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # 如果需要签名
        if self.secret_key:
            headers["X-Secret-Key"] = self.secret_key
        return headers
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        调用 LongCat 对话接口
        
        Args:
            messages: 对话消息列表
            temperature: 随机性 (0-1)
            max_tokens: 最大生成token数
            stream: 是否流式输出
            response_format: 响应格式 (如 {"type": "json_object"})
        """
        if not self.api_key:
            logger.warning("未配置 LONGCAT_API_KEY，使用模拟响应")
            return self._mock_response(messages)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        # 如果需要 JSON 输出
        if response_format and response_format.get("type") == "json_object":
            payload["response_format"] = response_format
            # 在 system prompt 中提示输出 JSON
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] += "\n请确保输出为有效的 JSON 格式。"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            elif "data" in result:
                # 某些版本的 API 格式
                return result["data"]["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected response format: {result}")
                return self._mock_response(messages)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LongCat API HTTP 错误: {e.response.status_code} - {e.response.text}")
            return self._mock_response(messages)
        except Exception as e:
            logger.error(f"LongCat API 调用失败: {e}")
            return self._mock_response(messages)
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        流式调用 LongCat 对话接口
        
        Yields:
            生成的文本片段
        """
        if not self.api_key:
            yield self._mock_response(messages)
            return
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉 "data: " 前缀
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"LongCat 流式调用失败: {e}")
            yield self._mock_response(messages)
    
    def _mock_response(self, messages: List[Dict]) -> str:
        """模拟响应（用于测试）"""
        last_message = messages[-1]["content"] if messages else ""
        
        if "问卷" in last_message or "questionnaire" in last_message.lower():
            return json.dumps({
                "next_question": "您家里目前有其他宠物吗？",
                "is_complete": False,
                "current_field": "other_pets",
                "suggested_options": ["没有", "有一只狗", "有一只猫", "有多只宠物"],
                "explanation": "了解您是否有养宠经验"
            }, ensure_ascii=False)
        
        elif "匹配" in last_message or "match" in last_message.lower():
            return json.dumps({
                "matches": [
                    {
                        "pet_id": "1",
                        "score": 92,
                        "reasons": ["活动量匹配", "适合有小孩的家庭"],
                        "concerns": ["需要较多运动空间"],
                        "compatibility": {"activity": 0.9, "space": 0.8, "experience": 0.95}
                    }
                ]
            }, ensure_ascii=False)
        
        elif "审核" in last_message or "review" in last_message.lower():
            return json.dumps({
                "passed": True,
                "score": 85,
                "risk_level": "low",
                "risk_points": [],
                "suggestions": ["建议定期回访"],
                "auto_approved": True
            }, ensure_ascii=False)
        
        return "{}"
    
    # ==================== 嵌入向量 (可选) ====================
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量
        用于相似度计算、RAG 等场景
        """
        if not self.api_key:
            # 返回模拟向量
            return [0.0] * 768
        
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                headers=self._get_headers(),
                json={
                    "model": "longcat-embedding",  # 嵌入模型名称
                    "input": text
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0]["embedding"]
            return [0.0] * 768
            
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            return [0.0] * 768


# 全局 LongCat 服务实例
longcat_service = LongCatService()
