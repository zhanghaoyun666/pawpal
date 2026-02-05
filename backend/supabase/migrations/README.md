# Supabase 数据库迁移

## 执行迁移脚本

### 方法1：使用 Supabase Dashboard（推荐）

1. 登录 [Supabase Dashboard](https://app.supabase.io)
2. 选择你的项目
3. 进入 SQL Editor
4. 新建查询
5. 复制 `20250205_ai_features.sql` 内容
6. 点击 Run

### 方法2：使用 Supabase CLI

```bash
# 安装 Supabase CLI
npm install -g supabase

# 登录
supabase login

# 链接项目
supabase link --project-ref your-project-ref

# 执行迁移
supabase db push
```

### 方法3：使用 psql

```bash
# 获取连接字符串（从 Supabase Dashboard -> Settings -> Database）
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" -f 20250205_ai_features.sql
```

## 迁移内容说明

### 创建的表

| 表名 | 说明 |
|-----|------|
| `adopter_profiles` | 领养人20维画像表 |
| `adoption_feedback` | 领养后反馈表 |
| `precheck_sessions` | AI预审会话状态表 |
| `ai_precheck_results` | AI预审结果表 |

### 修改的表

| 表名 | 修改内容 |
|-----|---------|
| `pets` | 添加12个新字段（体型、能量水平、护理需求等） |

### 关键特性

- ✅ 支持 pgvector 向量扩展（Embedding 存储）
- ✅ 完整的 RLS 行级安全策略
- ✅ 自动更新时间戳触发器
- ✅ 为现有数据生成默认值

## 验证安装

执行以下 SQL 验证：

```sql
-- 检查表是否创建成功
SELECT table_name 
FROM information.tables 
WHERE table_schema = 'public' 
AND table_name IN ('adopter_profiles', 'adoption_feedback', 'precheck_sessions', 'ai_precheck_results');

-- 检查 pets 表新字段
SELECT column_name 
FROM information.columns 
WHERE table_name = 'pets' 
AND column_name IN ('size_category', 'energy_level', 'pet_embedding', 'success_rate');

-- 检查向量扩展
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## 故障排除

### 问题1：pgvector 扩展未安装
```sql
-- 在 SQL Editor 中执行
CREATE EXTENSION IF NOT EXISTS vector;
```

### 问题2：权限不足
确保使用 `postgres` 角色或具有 `CREATE` 权限的角色执行。

### 问题3：现有数据冲突
脚本中使用了 `IF NOT EXISTS` 和 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，应该可以安全重跑。
