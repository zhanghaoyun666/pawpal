"""
模型下载脚本
首次运行前执行，下载本地 Embedding 模型
"""
import os
import sys


def download_embedding_model(model_name: str = "BAAI/bge-large-zh-v1.5"):
    """下载 Embedding 模型"""
    print(f"正在下载 Embedding 模型: {model_name}")
    print("这可能需要几分钟时间，取决于网络速度...")
    print()
    
    # 自动设置镜像源（如果在中国）
    if not os.getenv("HF_ENDPOINT"):
        print("正在使用 HuggingFace 镜像源...")
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print(f"HF_ENDPOINT={os.environ['HF_ENDPOINT']}")
        print()
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 下载模型（会自动缓存到 ~/.cache/torch/sentence_transformers/）
        model = SentenceTransformer(model_name)
        
        # 测试编码
        test_text = "这是一个测试句子"
        embedding = model.encode([test_text])
        
        print(f"✅ 模型下载成功！")
        print(f"   模型名称: {model_name}")
        print(f"   向量维度: {model.get_sentence_embedding_dimension()}")
        print(f"   测试文本: '{test_text}'")
        print(f"   测试向量: {embedding[0][:5]}... (前5个值)")
        print()
        print("模型已缓存到本地，下次启动时会自动加载。")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        print()
        print("可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 手动下载模型:")
        print("   - 访问 https://hf-mirror.com/BAAI/bge-large-zh-v1.5")
        print("   - 下载所有文件到本地目录")
        print("   - 设置环境变量: LOCAL_MODEL_PATH=你的本地路径")
        print()
        return False


def download_with_mirror():
    """使用镜像源下载"""
    # 设置镜像源
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    # 同时设置 HuggingFace 的其他镜像
    os.environ["HUGGINGFACE_HUB_ENDPOINT"] = "https://hf-mirror.com"
    
    print("=" * 60)
    print("PawPal AI 模型下载工具")
    print("=" * 60)
    print(f"使用镜像源: {os.environ['HF_ENDPOINT']}")
    print()
    
    # 检查是否使用本地模式
    embedding_mode = os.getenv("EMBEDDING_MODE", "local")
    
    if embedding_mode != "local":
        print(f"当前 EMBEDDING_MODE={embedding_mode}，不是本地模式，无需下载模型。")
        sys.exit(0)
    
    # 下载模型
    model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-zh-v1.5")
    success = download_embedding_model(model_name)
    
    if success:
        print()
        print("🎉 模型准备就绪，可以启动后端服务了！")
        print("   运行: uvicorn app.main:app --reload --port 8000")
    else:
        print()
        print("⚠️  模型下载失败，尝试使用备用方案...")
        print()
        
        # 尝试备选模型
        print("尝试下载更小的模型 BAAI/bge-small-zh-v1.5 ...")
        os.environ["EMBEDDING_MODEL_NAME"] = "BAAI/bge-small-zh-v1.5"
        success = download_embedding_model("BAAI/bge-small-zh-v1.5")
        
        if success:
            print()
            print("✅ 小模型下载成功！请修改 .env 使用小模型:")
            print("   EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5")
            print("   EMBEDDING_DIMENSION=512")
        else:
            print()
            print("❌ 所有下载方案均失败。")
            print("系统仍可使用模拟向量运行，但匹配质量会降低。")
            sys.exit(1)


if __name__ == "__main__":
    download_with_mirror()
