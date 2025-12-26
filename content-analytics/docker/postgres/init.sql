-- 初始化数据库
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建枚举类型
CREATE TYPE dataset_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE analysis_status AS ENUM ('pending', 'analyzing', 'ai_processing', 'completed', 'failed');
CREATE TYPE export_format AS ENUM ('excel', 'pdf', 'json');
CREATE TYPE export_status AS ENUM ('pending', 'processing', 'completed', 'failed');
