# Embedding 本地部署指南

## 简介

PawPal 支持两种 Embedding 模式：
- **本地部署**（推荐）：使用 BGE-large-zh 模型，无需 API Key，数据不出本地
- **API 调用**：使用 SiliconFlow、OpenAI 等第三方服务

## 快速开始（本地部署）

### 1. 安装依赖

```bash
cd backend

# 安装 Python 依赖（包含 PyTorch 和 sentence-transformers）
pip install -r requirements.txt
```

### 2. 下载模型（首次运行）

```bash
# 自动下载 BGE-large-zh 模型（约 1.2GB）
python download_models.py
```

模型会自动下载到 `~/.cache/torch/sentence_transformers/` 目录。

### 3. 配置环境变量

```bash
# backend/.env

# 使用本地 Embedding（无需 API Key）
EMBEDDING_MODE=local
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5
EMBEDDING_DIMENSION=1024
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

首次启动时会自动加载模型，可能需要 10-30 秒。

---

## 模型说明

### BGE-large-zh-v1.5

- **厂商**：北京智源人工智能研究院（BAAI）
- **类型**：开源中文 Embedding 模型
- **维度**：1024
- **大小**：约 1.2GB
- **性能**：中文语义理解优秀，适合宠物匹配场景
- **许可**：MIT 开源协议，可商用

### 硬件要求

| 配置 | 内存占用 | 推理速度 |
|-----|---------|---------|
| CPU (推荐) | ~2GB | ~50-100ms/文本 |
| GPU (可选) | ~2GB VRAM | ~10-20ms/文本 |

---

## 常见问题

### Q1: 下载模型很慢或失败？

**解决方案：**

```bash
# 方法一：使用 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com
python download_models.py

# 方法二：手动下载
# 1. 从 https://huggingface.co/BAAI/bge-large-zh-v1.5 下载模型
# 2. 解压到 ~/.cache/torch/sentence_transformers/BAAI__bge-large-zh-v1.5/
```

### Q2: 内存不足？

**解决方案：**

使用更小的模型：

```bash
# backend/.env
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5  # 仅 100MB
EMBEDDING_DIMENSION=512
```

### Q3: 想使用 GPU 加速？

**解决方案：**

```bash
# 安装 GPU 版 PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 模型会自动使用 GPU（如果可用）
```

### Q4: 如何验证 Embedding 正常工作？

```bash
# 运行测试脚本
python test_ai_features.py

# 或者手动测试
curl http://localhost:8000/api/ai/v2/health
```

---

## 切换回 API 模式

如果不想本地部署，可以切换到 API 模式：

### SiliconFlow（推荐，国内可用）

```bash
# 1. 注册获取 API Key：https://siliconflow.cn

# 2. 修改 .env
EMBEDDING_MODE=api
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=sk-your-key
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5
EMBEDDING_DIMENSION=1024
```

### OpenAI

```bash
EMBEDDING_MODE=api
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-key
EMBEDDING_MODEL_NAME=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

---

## 性能优化建议

### 1. 模型缓存
- 模型首次加载后会缓存在内存中
- 不要频繁重启服务

### 2. 批量处理
- 使用 `get_embeddings_batch()` 批量编码，比单条快 5-10 倍

### 3. 向量缓存
- Embedding 服务内置了 LRU 缓存
- 相同文本不会重复编码

### 4. 数据库索引
- pgvector 已配置 ivfflat 索引
- 大规模数据时相似度搜索仍然很快

---

## 故障排除

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| `ModuleNotFoundError: No module named 'sentence_transformers'` | 依赖未安装 | `pip install sentence-transformers` |
| `CUDA out of memory` | GPU 显存不足 | 使用 CPU 模式：`export CUDA_VISIBLE_DEVICES=""` |
| 模型下载卡住 | 网络问题 | 使用镜像源或手动下载 |
| 相似度计算全为 0 | 模型未加载 | 检查日志，重新下载模型 |

---

## 参考

- [BGE 模型官方文档](https://github.com/FlagOpen/FlagEmbedding)
- [Sentence-Transformers 文档](https://www.sbert.net/)
- [pgvector 文档](https://github.com/pgvector/pgvector)
