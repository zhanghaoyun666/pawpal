"""
AI 功能测试脚本
验证数据库连接和 AI 服务是否正常工作
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import supabase
from app.services.matching_engine import matching_engine
from app.services.precheck_engine import precheck_engine
from app.services.embedding_service import embedding_service


async def test_database():
    """测试数据库连接"""
    print("=" * 50)
    print("测试数据库连接...")
    
    try:
        # 测试查询 pets 表
        result = supabase.table("pets").select("*").limit(1).execute()
        print(f"✅ 数据库连接正常，pets 表有数据")
        
        # 检查新字段
        pet = result.data[0] if result.data else {}
        new_fields = ['size_category', 'energy_level', 'pet_embedding', 'success_rate']
        missing = [f for f in new_fields if f not in pet]
        
        if missing:
            print(f"⚠️  pets 表缺少字段: {missing}")
        else:
            print(f"✅ pets 表新字段已添加")
        
        # 检查新表
        tables = ['adopter_profiles', 'adoption_feedback', 'precheck_sessions', 'ai_precheck_results']
        for table in tables:
            try:
                supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table} 表存在")
            except Exception as e:
                print(f"❌ {table} 表错误: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


async def test_embedding():
    """测试 Embedding 服务"""
    print("\n" + "=" * 50)
    print("测试 Embedding 服务...")
    
    try:
        text = "这是一个测试文本"
        embedding = await embedding_service.get_embedding(text, use_cache=False)
        
        if len(embedding) == 1024:
            print(f"✅ Embedding 生成正常，维度: {len(embedding)}")
            print(f"   前5个值: {embedding[:5]}")
        else:
            print(f"⚠️  Embedding 维度异常: {len(embedding)}，期望 1024")
        
        # 测试相似度计算
        embedding2 = await embedding_service.get_embedding("这是另一个测试文本", use_cache=False)
        sim = embedding_service.cosine_similarity(embedding, embedding2)
        print(f"✅ 余弦相似度计算正常: {sim:.4f}")
        
        return True
    except Exception as e:
        print(f"❌ Embedding 服务失败: {e}")
        return False


async def test_matching():
    """测试匹配引擎"""
    print("\n" + "=" * 50)
    print("测试匹配引擎...")
    
    try:
        # 模拟领养人画像
        adopter = {
            "living_space": "medium_apartment",
            "has_yard": False,
            "is_renting": True,
            "landlord_allows_pets": True,
            "budget_level": "medium",
            "income_stability": "stable",
            "daily_time_available": 3,
            "work_schedule": "regular",
            "work_hours_per_day": 8,
            "experience_level": "beginner",
            "previous_pets": [],
            "training_willingness": "medium",
            "family_status": "couple",
            "household_size": 2,
            "preferred_size": "medium",
            "preferred_age": "young",
            "preferred_temperament": ["calm", "friendly"],
            "activity_level": "medium",
            "other_pets": [],
            "noise_tolerance": "medium",
            "shedding_tolerance": "medium",
            "grooming_willingness": "medium"
        }
        
        # 模拟宠物
        pet = {
            "id": "test-pet-1",
            "name": "测试金毛",
            "species": "dog",
            "breed": "金毛寻回犬",
            "age_months": 24,
            "size_category": "large",
            "weight_kg": 30,
            "gender": "male",
            "temperament": ["friendly", "calm", "gentle"],
            "energy_level": "medium",
            "sociability": "outgoing",
            "trainability": "easy",
            "shedding_level": "high",
            "grooming_needs": "medium",
            "exercise_needs": "medium",
            "good_with_kids": True,
            "good_with_dogs": True,
            "good_with_cats": True,
            "good_with_strangers": True,
            "special_needs": [],
            "min_space_requirement": "large_apartment",
            "needs_yard": False,
            "success_rate": 0.8
        }
        
        result = await matching_engine.calculate_match(adopter, pet)
        
        print(f"✅ 匹配计算成功")
        print(f"   总分: {result.overall_score}")
        print(f"   硬性条件: {result.hard_constraint_score}")
        print(f"   软性偏好: {result.soft_preference_score}")
        print(f"   历史得分: {result.historical_score}")
        print(f"   是否通过硬性条件: {result.passed_hard_constraints}")
        print(f"   匹配理由: {result.match_reasons}")
        
        return True
    except Exception as e:
        print(f"❌ 匹配引擎失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_precheck():
    """测试预审引擎"""
    print("\n" + "=" * 50)
    print("测试预审引擎...")
    
    try:
        # 创建会话
        session_id = precheck_engine.create_session("test-user", "test-pet")
        print(f"✅ 预审会话创建成功: {session_id}")
        
        # 第一轮对话
        result = await precheck_engine.process_message(session_id, "")
        print(f"✅ 第一轮对话")
        print(f"   状态: {result['state']}")
        print(f"   AI回复: {result['response'][:100]}...")
        
        # 用户回复
        result = await precheck_engine.process_message(session_id, "我是上班族，住在公寓里")
        print(f"✅ 第二轮对话")
        print(f"   状态: {result['state']}")
        print(f"   已收集数据: {list(result.get('collected_data', {}).keys())}")
        
        return True
    except Exception as e:
        print(f"❌ 预审引擎失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("🚀 PawPal AI 功能测试")
    print("=" * 50)
    
    results = []
    
    # 测试数据库
    results.append(("数据库", await test_database()))
    
    # 测试 Embedding
    results.append(("Embedding", await test_embedding()))
    
    # 测试匹配引擎
    results.append(("匹配引擎", await test_matching()))
    
    # 测试预审引擎
    results.append(("预审引擎", await test_precheck()))
    
    # 汇总
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！AI 功能已就绪。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
