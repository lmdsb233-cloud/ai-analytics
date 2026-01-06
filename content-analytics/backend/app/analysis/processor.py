import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime


class DataProcessor:
    """数据预处理器"""
    
    # Excel列名映射
    COLUMN_MAPPING = {
        'data_id': 'data_id',
        '标题': 'content_title',
        '发文时间': 'publish_time',
        '发文链接': 'publish_link',
        '内容形式': 'content_type',
        '发文类型': 'post_type',
        '素材来源': 'source',
        '款式信息': 'style_info',
        # 兼容有/无斜杠的统计列命名
        '7天阅读/播放': 'read_7d',
        '7天阅读播放': 'read_7d',
        '7天互动': 'interact_7d',
        '7天好物访问': 'visit_7d',
        '7天好物想要': 'want_7d',
        '14天阅读/播放': 'read_14d',
        '14天阅读播放': 'read_14d',
        '14天互动': 'interact_14d',
        '14天好物访问': 'visit_14d',
        '14天好物想要': 'want_14d',
    }
    
    # 数值型指标列
    NUMERIC_COLUMNS = [
        'read_7d', 'interact_7d', 'visit_7d', 'want_7d',
        'read_14d', 'interact_14d', 'visit_14d', 'want_14d'
    ]
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.processed_df = None
    
    def rename_columns(self) -> 'DataProcessor':
        """重命名列"""
        rename_dict = {}
        for col in self.df.columns:
            if col in self.COLUMN_MAPPING:
                rename_dict[col] = self.COLUMN_MAPPING[col]
        self.df = self.df.rename(columns=rename_dict)
        return self
    
    def clean_numeric_columns(self) -> 'DataProcessor':
        """清洗数值型列"""
        for col in self.NUMERIC_COLUMNS:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        return self
    
    def parse_datetime(self) -> 'DataProcessor':
        """解析日期时间"""
        if 'publish_time' in self.df.columns:
            self.df['publish_time'] = pd.to_datetime(
                self.df['publish_time'], 
                errors='coerce'
            )
        return self
    
    def handle_missing_values(self) -> 'DataProcessor':
        """处理缺失值"""
        # 字符串列用空字符串填充
        string_cols = ['content_title', 'content_type', 'post_type', 'source', 'style_info', 'publish_link']
        for col in string_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna('')
        
        # 数值列保留NaN，后续分析时会处理
        return self
    
    def validate(self) -> Dict[str, Any]:
        """验证数据"""
        errors = []
        warnings = []
        
        # 检查必要列
        if 'data_id' not in self.df.columns:
            errors.append("缺少必要列: data_id")
        
        # 检查data_id唯一性
        if 'data_id' in self.df.columns:
            duplicates = self.df['data_id'].duplicated().sum()
            if duplicates > 0:
                warnings.append(f"发现 {duplicates} 条重复的data_id")
        
        # 检查数值列
        for col in self.NUMERIC_COLUMNS:
            if col in self.df.columns:
                null_count = self.df[col].isna().sum()
                if null_count > 0:
                    warnings.append(f"列 {col} 有 {null_count} 个空值")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(self.df)
        }
    
    def process(self) -> pd.DataFrame:
        """执行完整处理流程"""
        self.rename_columns()
        self.clean_numeric_columns()
        self.parse_datetime()
        self.handle_missing_values()
        self.processed_df = self.df
        return self.processed_df
    
    def to_records(self) -> List[Dict[str, Any]]:
        """转换为记录列表"""
        if self.processed_df is None:
            self.process()
        
        records = []
        for _, row in self.processed_df.iterrows():
            record = {}
            for col in self.processed_df.columns:
                val = row[col]
                if pd.isna(val):
                    record[col] = None
                elif isinstance(val, (pd.Timestamp, datetime)):
                    record[col] = val
                else:
                    record[col] = val
            records.append(record)
        
        return records
