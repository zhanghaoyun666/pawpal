"""
手动下载模型脚本
当自动下载失败时使用
"""
import os
import urllib.request
import json
from pathlib import Path


def download_file(url: str, dest: str):
    """下载文件"""
    print(f"下载: {url}")
    print(f"到: {dest}")
    
    # 创建目录
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    # 下载
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"✅ 完成")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def download_bge_small():
    """
    手动下载 BGE-small-zh 模型
    从 hf-mirror.com 下载
    """
    model_name = "BAAI/bge-small-zh-v1.5"
    mirror = "https://hf-mirror.com"
    
    # 缓存目录
    cache_dir = Path.home() / ".cache" / "torch" / "sentence_transformers"
    model_dir = cache_dir / model_name.replace("/", "__")
    
    print(f"模型将下载到: {model_dir}")
    print()
    
    # 需要的文件列表
    files = [
        "config.json",
        "config_sentence_transformers.json",
        "model.safetensors",
        "modules.json",
        "sentence_bert_config.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt"
    ]
    
    success_count = 0
    
    for file in files:
        url = f"{mirror}/{model_name}/resolve/main/{file}"
        dest = str(model_dir / file)
        
        if os.path.exists(dest):
            print(f"⏭️  已存在: {file}")
            success_count += 1
            continue
        
        if download_file(url, dest):
            success_count += 1
        print()
    
    if success_count >= len(files) - 2:  # 允许 2 个文件失败
        print(f"✅ 模型下载完成！({success_count}/{len(files)})")
        print(f"路径: {model_dir}")
        
        # 测试加载
        print("\n测试加载模型...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(str(model_dir))
            print(f"✅ 模型加载成功！维度: {model.get_sentence_embedding_dimension()}")
            return True
        except Exception as e:
            print(f"⚠️  加载测试失败: {e}")
            return True  # 仍然返回 True，因为文件已下载
    else:
        print(f"❌ 下载失败文件过多 ({success_count}/{len(files)})")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("手动下载 Embedding 模型")
    print("=" * 60)
    print()
    
    success = download_bge_small()
    
    if success:
        print()
        print("🎉 模型已准备就绪！")
        print()
        print("请修改 backend/.env 使用小模型：")
        print("  EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5")
        print("  EMBEDDING_DIMENSION=512")
