"""
Embedding 向量服务
支持本地部署 (BGE-large-zh) 或 API 调用
"""
import os
import logging
from typing import List, Dict, Optional
import numpy as np
from numpy.linalg import norm
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Embedding 配置
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "local")  # local 或 api
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-zh-v1.5")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

# 本地模型缓存
_local_model = None


class LocalEmbeddingModel:
    """本地 Embedding 模型封装"""
    
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载本地模型"""
        global _local_model
        
        if _local_model is not None:
            self.model = _local_model
            logger.info(f"使用缓存的本地模型: {self.model_name}")
            return
        
        # 检查是否为模拟模式
        if self.model_name == "mocker":
            logger.warning("⚠️ 使用模拟 Embedding 模式（随机向量）")
            self.model = None
            return
        
        try:
            logger.info(f"正在加载本地 Embedding 模型: {self.model_name}")
            
            # 设置镜像源（如果未设置）
            if not os.getenv("HF_ENDPOINT"):
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                os.environ["HUGGINGFACE_HUB_ENDPOINT"] = "https://hf-mirror.com"
            
            # 延迟导入，避免启动时加载
            from sentence_transformers import SentenceTransformer
            
            # 自动下载模型到本地缓存（~/.cache/torch/sentence_transformers/）
            self.model = SentenceTransformer(self.model_name)
            _local_model = self.model
            
            logger.info(f"✅ 本地模型加载成功: {self.model_name}")
            logger.info(f"   模型维度: {self.model.get_sentence_embedding_dimension()}")
            
        except Exception as e:
            logger.error(f"❌ 加载本地模型失败: {e}")
            logger.warning("⚠️ 将使用模拟 Embedding 模式（随机向量）")
            self.model = None
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        编码文本为向量
        
        Args:
            texts: 文本列表
        
        Returns:
            向量列表
        """
        if isinstance(texts, str):
            texts = [texts]
        
        # 模拟模式：返回随机但一致的向量
        if self.model is None:
            import hashlib
            results = []
            for text in texts:
                # 使用文本哈希生成随机种子，确保相同文本得到相同向量
                seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
                np.random.seed(seed)
                vec = np.random.randn(self.dimension)
                vec = vec / np.linalg.norm(vec)  # 归一化
                results.append(vec.tolist())
            return results
        
        # 使用模型编码
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # 归一化，便于计算余弦相似度
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()


class EmbeddingService:
    """Embedding 服务 - 支持本地或 API 模式"""
    
    def __init__(self):
        self.mode = EMBEDDING_MODE
        self.api_key = EMBEDDING_API_KEY
        self.base_url = EMBEDDING_BASE_URL
        self.model_name = EMBEDDING_MODEL_NAME
        self.dimension = EMBEDDING_DIMENSION
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # 本地模型实例
        self._local_model: Optional[LocalEmbeddingModel] = None
        
        # 本地缓存
        self._cache: Dict[str, List[float]] = {}
        
        logger.info(f"Embedding 服务初始化完成，模式: {self.mode}")
    
    def _get_local_model(self) -> LocalEmbeddingModel:
        """获取本地模型（懒加载）"""
        if self._local_model is None:
            self._local_model = LocalEmbeddingModel(self.model_name)
        return self._local_model
    
    async def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        获取文本的 Embedding 向量
        
        Args:
            text: 输入文本
            use_cache: 是否使用缓存
        
        Returns:
            向量列表
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        # 检查缓存
        cache_key = hash(text)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # 根据模式选择获取方式
        if self.mode == "local":
            embedding = await self._get_local_embedding(text)
        else:
            embedding = await self._call_embedding_api(text)
        
        # 缓存结果
        if use_cache:
            self._cache[cache_key] = embedding
        
        return embedding
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取 Embedding"""
        if self.mode == "local":
            return await self._get_local_embeddings_batch(texts)
        else:
            import asyncio
            tasks = [self.get_embedding(text) for text in texts]
            return await asyncio.gather(*tasks)
    
    async def _get_local_embedding(self, text: str) -> List[float]:
        """使用本地模型获取 Embedding"""
        try:
            model = self._get_local_model()
            embeddings = model.encode([text])
            return embeddings[0]
        except Exception as e:
            logger.error(f"本地模型编码失败: {e}")
            # 降级为随机向量（避免系统崩溃）
            import random
            return [random.uniform(-0.1, 0.1) for _ in range(self.dimension)]
    
    async def _get_local_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量本地编码"""
        try:
            model = self._get_local_model()
            
            # 在线程池中执行，避免阻塞事件循环
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                embeddings = await loop.run_in_executor(
                    pool, 
                    lambda: model.encode(texts)
                )
            
            return embeddings
        except Exception as e:
            logger.error(f"本地模型批量编码失败: {e}")
            import random
            return [[random.uniform(-0.1, 0.1) for _ in range(self.dimension)] for _ in texts]
    
    async def _call_embedding_api(self, text: str) -> List[float]:
        """调用 API 获取 Embedding"""
        if not self.api_key:
            logger.warning("未配置 EMBEDDING_API_KEY，返回零向量")
            return [0.0] * self.dimension
        
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "input": text
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0]["embedding"]
            
            logger.error(f"Embedding API 返回格式异常: {result}")
            return [0.0] * self.dimension
            
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            return [0.0] * self.dimension
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        注意：如果向量已归一化，可以直接用点积
        """
        a = np.array(vec1)
        b = np.array(vec2)
        
        # 处理零向量
        if norm(a) == 0 or norm(b) == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm(a) * norm(b)))
    
    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算欧氏距离"""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(norm(a - b))
    
    async def find_similar(
        self,
        query_embedding: List[float],
        candidates: List[tuple],
        top_k: int = 3
    ) -> List[tuple]:
        """从候选中找到最相似的"""
        similarities = []
        for item_id, embedding in candidates:
            sim = self.cosine_similarity(query_embedding, embedding)
            similarities.append((item_id, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# 全局 Embedding 服务实例
embedding_service = EmbeddingService()


# ==================== 画像文本化工具 ====================

def adopter_profile_to_text(profile: Dict) -> str:
    """将领养人画像转换为文本描述"""
    texts = []
    
    living_map = {
        "small_apartment": "住在小公寓",
        "medium_apartment": "住在中等公寓",
        "large_apartment": "住在大公寓",
        "house_with_yard": "住带院子的房子",
        "rural": "住在农村"
    }
    if profile.get("living_space"):
        texts.append(living_map.get(profile["living_space"], ""))
    
    if profile.get("has_yard"):
        texts.append("有院子")
    
    exp_map = {
        "none": "没有养宠经验",
        "beginner": "有一些养宠经验",
        "intermediate": "养宠经验较丰富",
        "experienced": "养宠经验丰富"
    }
    if profile.get("experience_level"):
        texts.append(exp_map.get(profile["experience_level"], ""))
    
    daily_time = profile.get("daily_time_available", 0)
    if daily_time > 0:
        if daily_time >= 4:
            texts.append(f"每天有{daily_time}小时陪伴宠物，时间充裕")
        elif daily_time >= 2:
            texts.append(f"每天有{daily_time}小时陪伴宠物")
        else:
            texts.append(f"每天只有{daily_time}小时陪伴宠物，时间较少")
    
    family_map = {
        "single": "单身独居",
        "couple": "和伴侣同住",
        "with_kids_young": "有年幼的孩子",
        "with_kids_old": "有较大的孩子",
        "with_elderly": "和老人同住",
        "multi_gen": "三代同堂"
    }
    if profile.get("family_status"):
        texts.append(family_map.get(profile["family_status"], ""))
    
    activity_map = {
        "low": "喜欢安静的生活",
        "medium": "喜欢适度的活动",
        "high": "喜欢活跃的运动"
    }
    if profile.get("activity_level"):
        texts.append(activity_map.get(profile["activity_level"], ""))
    
    if profile.get("preferred_temperament"):
        traits = ", ".join(profile["preferred_temperament"])
        texts.append(f"希望宠物性格：{traits}")
    
    return "。".join([t for t in texts if t])


def pet_profile_to_text(pet: Dict) -> str:
    """将宠物档案转换为文本描述"""
    texts = []
    
    texts.append(f"{pet.get('breed', '')}")
    
    age_months = pet.get("age_months", 0)
    if age_months < 6:
        texts.append("幼年宠物")
    elif age_months < 24:
        texts.append("青年宠物")
    elif age_months < 84:
        texts.append("成年宠物")
    else:
        texts.append("老年宠物")
    
    size_map = {
        "tiny": "迷你体型",
        "small": "小型宠物",
        "medium": "中型宠物",
        "large": "大型宠物",
        "xlarge": "超大型宠物"
    }
    if pet.get("size_category"):
        texts.append(size_map.get(pet["size_category"], ""))
    
    temperament = pet.get("temperament", [])
    if temperament:
        texts.append(f"性格：{', '.join(temperament)}")
    
    energy_map = {
        "low": "能量水平低，比较安静",
        "medium": "能量水平中等",
        "high": "能量水平高，需要大量运动"
    }
    if pet.get("energy_level"):
        texts.append(energy_map.get(pet["energy_level"], ""))
    
    shedding_map = {
        "none": "不掉毛",
        "low": "掉毛少",
        "medium": "正常掉毛",
        "high": "掉毛多"
    }
    if pet.get("shedding_level"):
        texts.append(shedding_map.get(pet["shedding_level"], ""))
    
    if pet.get("good_with_kids"):
        texts.append("适合有孩子的家庭")
    if pet.get("good_with_dogs"):
        texts.append("可以和其他狗相处")
    
    return "。".join([t for t in texts if t])
