# 内容账号数据分析 + AI 辅助决策系统

## 项目概述

一个用于内容账号数据分析和AI辅助决策的网页服务。用户可以上传Excel数据，系统进行数据分析后，调用大模型API生成优化建议。

## 技术栈

### 后端
- **框架**: Python + FastAPI
- **ORM**: SQLAlchemy
- **数据库**: PostgreSQL
- **异步任务**: Celery + Redis
- **认证**: JWT

### 前端
- **框架**: Vue 3 + TypeScript
- **UI组件**: Element Plus
- **HTTP客户端**: Axios
- **状态管理**: Pinia
- **路由**: Vue Router

### AI服务
- **默认模型**: DeepSeek API
- **抽象层**: 支持切换 OpenAI / 其他模型

### 部署
- Docker + Docker Compose

## 项目结构

```
content-analytics/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py        # 认证接口
│   │   │   │   ├── datasets.py    # 数据集接口
│   │   │   │   ├── analyses.py    # 分析接口
│   │   │   │   ├── posts.py       # 笔记接口
│   │   │   │   └── exports.py     # 导出接口
│   │   │   └── deps.py            # 依赖注入
│   │   ├── core/              # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # 配置管理
│   │   │   ├── security.py        # 安全/JWT
│   │   │   └── exceptions.py      # 异常处理
│   │   ├── models/            # 数据库模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── dataset.py
│   │   │   ├── post.py
│   │   │   ├── analysis.py
│   │   │   └── export.py
│   │   ├── schemas/           # Pydantic模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── dataset.py
│   │   │   ├── post.py
│   │   │   ├── analysis.py
│   │   │   └── common.py
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── dataset_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── ai_service.py
│   │   │   └── export_service.py
│   │   ├── analysis/          # 数据分析模块
│   │   │   ├── __init__.py
│   │   │   ├── processor.py       # 数据预处理
│   │   │   ├── calculator.py      # 指标计算
│   │   │   ├── anomaly.py         # 异常检测
│   │   │   └── aggregator.py      # 数据聚合
│   │   ├── ai/                # AI模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Provider基类
│   │   │   ├── deepseek.py        # DeepSeek实现
│   │   │   ├── openai.py          # OpenAI实现
│   │   │   ├── factory.py         # 工厂模式
│   │   │   └── prompts.py         # Prompt模板
│   │   ├── tasks/             # Celery异步任务
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── dataset_tasks.py
│   │   │   ├── analysis_tasks.py
│   │   │   └── ai_tasks.py
│   │   ├── db/                # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── utils/             # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── excel.py           # Excel解析
│   │   │   └── validators.py      # 数据校验
│   │   └── main.py            # 应用入口
│   ├── alembic/               # 数据库迁移
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── tests/                 # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   └── test_services/
│   ├── uploads/               # 上传文件目录
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # 前端服务
│   ├── src/
│   │   ├── api/               # API请求
│   │   │   ├── index.ts
│   │   │   ├── auth.ts
│   │   │   ├── datasets.ts
│   │   │   ├── analyses.ts
│   │   │   └── exports.ts
│   │   ├── assets/            # 静态资源
│   │   │   └── styles/
│   │   ├── components/        # 通用组件
│   │   │   ├── common/
│   │   │   ├── charts/
│   │   │   └── layout/
│   │   ├── composables/       # 组合式函数
│   │   │   ├── useAuth.ts
│   │   │   └── useAnalysis.ts
│   │   ├── router/            # 路由
│   │   │   └── index.ts
│   │   ├── stores/            # Pinia状态
│   │   │   ├── auth.ts
│   │   │   ├── dataset.ts
│   │   │   └── analysis.ts
│   │   ├── types/             # TypeScript类型
│   │   │   └── index.ts
│   │   ├── views/             # 页面组件
│   │   │   ├── LoginView.vue
│   │   │   ├── DatasetsView.vue
│   │   │   ├── AnalysisConfigView.vue
│   │   │   ├── AnalysisResultView.vue
│   │   │   ├── PostDetailView.vue
│   │   │   └── ExportView.vue
│   │   ├── utils/             # 工具函数
│   │   │   └── index.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
│
├── docker/                     # Docker配置
│   ├── nginx/
│   │   └── nginx.conf
│   └── postgres/
│       └── init.sql
│
├── docker-compose.yml          # 容器编排
├── docker-compose.dev.yml      # 开发环境
├── .gitignore
└── README.md
```

## 核心业务流程

```
用户登录 → 上传Excel → 数据解析入库 → 数据分析(非AI) → AI生成建议 → 展示结果 → 导出报告
```

## 数据库模型

### users (用户表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | String | 用户名 |
| email | String | 邮箱 |
| hashed_password | String | 密码哈希 |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |

### datasets (数据集表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户ID(外键) |
| name | String | 数据集名称 |
| file_path | String | 原始文件路径 |
| status | Enum | 状态(pending/processing/completed/failed) |
| row_count | Integer | 行数 |
| created_at | DateTime | 创建时间 |

### posts (笔记表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| dataset_id | UUID | 数据集ID(外键) |
| data_id | String | 原始data_id |
| publish_time | DateTime | 发文时间 |
| publish_link | String | 发文链接 |
| content_type | String | 内容形式 |
| post_type | String | 发文类型 |
| source | String | 素材来源 |
| style_info | String | 款式信息 |
| read_7d | Float | 7天阅读/播放 |
| interact_7d | Float | 7天互动 |
| visit_7d | Float | 7天好物访问 |
| want_7d | Float | 7天好物想要 |
| read_14d | Float | 14天阅读/播放 |
| interact_14d | Float | 14天互动 |
| visit_14d | Float | 14天好物访问 |
| want_14d | Float | 14天好物想要 |

### analyses (分析任务表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| dataset_id | UUID | 数据集ID(外键) |
| user_id | UUID | 用户ID(外键) |
| status | Enum | 状态 |
| config | JSON | 分析配置 |
| created_at | DateTime | 创建时间 |
| completed_at | DateTime | 完成时间 |

### analysis_results (分析结果表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_id | UUID | 分析任务ID(外键) |
| post_id | UUID | 笔记ID(外键) |
| performance | String | 表现评级 |
| result_data | JSON | 结构化分析结果 |

### ai_outputs (AI输出表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_result_id | UUID | 分析结果ID(外键) |
| summary | Text | 一句话结论 |
| strengths | JSON | 好在哪 |
| weaknesses | JSON | 差在哪 |
| suggestions | JSON | 优化建议 |
| raw_response | Text | 原始响应 |
| model_name | String | 使用的模型 |
| created_at | DateTime | 创建时间 |

### exports (导出记录表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_id | UUID | 分析任务ID(外键) |
| user_id | UUID | 用户ID(外键) |
| file_path | String | 导出文件路径 |
| format | String | 导出格式 |
| created_at | DateTime | 创建时间 |

## API 设计

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

### 数据集
- `POST /api/v1/datasets/upload` - 上传Excel
- `GET /api/v1/datasets` - 获取数据集列表
- `GET /api/v1/datasets/{id}` - 获取数据集详情
- `DELETE /api/v1/datasets/{id}` - 删除数据集

### 分析
- `POST /api/v1/analyses` - 创建分析任务
- `GET /api/v1/analyses` - 获取分析列表
- `GET /api/v1/analyses/{id}` - 获取分析详情
- `GET /api/v1/analyses/{id}/results` - 获取分析结果
- `POST /api/v1/analyses/{id}/ai` - 触发AI分析

### 笔记
- `GET /api/v1/posts/{post_id}` - 获取笔记详情
- `GET /api/v1/posts/{post_id}/ai-output` - 获取笔记AI输出

### 导出
- `POST /api/v1/analyses/{id}/export` - 导出分析报告
- `GET /api/v1/exports/{id}/download` - 下载导出文件

## 快速开始

### 开发环境启动步骤

#### 1. 启动基础服务 (PostgreSQL + Redis)
```bash
# Windows
start-dev.bat

# Linux/Mac
chmod +x start-dev.sh && ./start-dev.sh

# 或手动启动
docker-compose -f docker-compose.dev.yml up -d
```

#### 2. 后端启动
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 复制并配置环境变量
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
# 编辑 .env 文件，配置数据库和AI API密钥

# 初始化数据库
python scripts/init_db.py

# 创建测试用户 (用户名: admin, 密码: admin123)
python scripts/create_user.py

# 启动后端服务
uvicorn app.main:app --reload
# 或
python run.py
```

#### 3. 启动Celery Worker (新终端)
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

#### 4. 前端启动 (新终端)
```bash
cd frontend

# 安装依赖
npm install

# 复制配置文件
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac

# 启动开发服务器
npm run dev
```

#### 5. 访问系统
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/api/docs
- 默认账号: admin / admin123

### 生产部署

```bash
# 配置环境变量
export SECRET_KEY=your-production-secret-key
export DEEPSEEK_API_KEY=your-api-key

# 启动所有服务
docker-compose up -d --build
```

## 环境变量

### 后端 (.env)
```
DATABASE_URL=postgresql://user:pass@localhost:5432/content_analytics
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

### 前端 (.env)
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```
