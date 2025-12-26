import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


class MetricsCalculator:
    """指标计算器"""
    
    METRIC_NAMES = {
        'read_7d': '7天阅读',
        'interact_7d': '7天互动',
        'visit_7d': '7天好物访问',
        'want_7d': '7天好物想要',
        'read_14d': '14天阅读',
        'interact_14d': '14天互动',
        'visit_14d': '14天好物访问',
        'want_14d': '14天好物想要'
    }
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.stats = {}
    
    def calculate_basic_stats(self) -> Dict[str, Dict[str, float]]:
        """计算基础统计量"""
        metrics = list(self.METRIC_NAMES.keys())
        
        for metric in metrics:
            if metric in self.df.columns:
                series = self.df[metric].dropna()
                if len(series) > 0:
                    self.stats[metric] = {
                        'mean': float(series.mean()),
                        'median': float(series.median()),
                        'std': float(series.std()) if len(series) > 1 else 0,
                        'min': float(series.min()),
                        'max': float(series.max()),
                        'q25': float(series.quantile(0.25)),
                        'q75': float(series.quantile(0.75)),
                        'q10': float(series.quantile(0.10)),
                        'q90': float(series.quantile(0.90)),
                        'count': int(len(series))
                    }
        
        return self.stats
    
    def calculate_group_stats(self, group_by: str) -> Dict[str, Dict[str, Dict[str, float]]]:
        """按分组计算统计量"""
        if group_by not in self.df.columns:
            return {}
        
        group_stats = {}
        metrics = list(self.METRIC_NAMES.keys())
        
        for group_name, group_df in self.df.groupby(group_by):
            if pd.isna(group_name) or group_name == '':
                group_name = '未分类'
            
            group_stats[str(group_name)] = {}
            
            for metric in metrics:
                if metric in group_df.columns:
                    series = group_df[metric].dropna()
                    if len(series) > 0:
                        group_stats[str(group_name)][metric] = {
                            'mean': float(series.mean()),
                            'median': float(series.median()),
                            'count': int(len(series))
                        }
        
        return group_stats
    
    def compare_to_baseline(
        self, 
        row: pd.Series, 
        baseline: str = 'mean'
    ) -> Dict[str, str]:
        """与基准比较"""
        comparison = {}
        
        for metric, stat in self.stats.items():
            if metric in row and pd.notna(row[metric]):
                value = row[metric]
                base_value = stat[baseline]
                
                if base_value != 0:
                    diff_percent = ((value - base_value) / base_value) * 100
                    if diff_percent > 0:
                        comparison[self.METRIC_NAMES[metric]] = f"+{diff_percent:.0f}%"
                    else:
                        comparison[self.METRIC_NAMES[metric]] = f"{diff_percent:.0f}%"
        
        return comparison
    
    def get_percentile_rank(self, row: pd.Series) -> Dict[str, float]:
        """获取百分位排名"""
        ranks = {}
        
        for metric in self.stats.keys():
            if metric in row and pd.notna(row[metric]):
                value = row[metric]
                series = self.df[metric].dropna()
                rank = (series < value).mean() * 100
                ranks[metric] = round(rank, 1)
        
        return ranks
