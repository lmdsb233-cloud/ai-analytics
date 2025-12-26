import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple


class AnomalyDetector:
    """异常检测器"""
    
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
    
    def __init__(
        self, 
        stats: Dict[str, Dict[str, float]],
        top_threshold: float = 0.9,
        bottom_threshold: float = 0.1
    ):
        self.stats = stats
        self.top_threshold = top_threshold
        self.bottom_threshold = bottom_threshold
    
    def detect_anomalies(self, row: pd.Series) -> Dict[str, Any]:
        """检测单行数据的异常"""
        highlights = []  # 表现突出的指标
        problems = []    # 表现较差的指标
        
        for metric, stat in self.stats.items():
            if metric not in row or pd.isna(row[metric]):
                continue
            
            value = row[metric]
            q90 = stat.get('q90', stat['max'])
            q10 = stat.get('q10', stat['min'])
            
            metric_name = self.METRIC_NAMES.get(metric, metric)
            
            # 高于90分位数
            if value >= q90:
                highlights.append(metric_name)
            # 低于10分位数
            elif value <= q10:
                problems.append(metric_name)
        
        return {
            'highlight_metrics': highlights,
            'problem_metrics': problems
        }
    
    def determine_performance(
        self, 
        row: pd.Series,
        primary_metrics: List[str] = None
    ) -> str:
        """判断整体表现"""
        if primary_metrics is None:
            primary_metrics = ['read_7d', 'interact_7d']
        
        scores = []
        
        for metric in primary_metrics:
            if metric not in self.stats or metric not in row:
                continue
            if pd.isna(row[metric]):
                continue
            
            value = row[metric]
            stat = self.stats[metric]
            median = stat['median']
            
            if median == 0:
                continue
            
            # 计算相对于中位数的比值
            ratio = value / median
            scores.append(ratio)
        
        if not scores:
            return "无法判断"
        
        avg_score = np.mean(scores)
        
        if avg_score >= 1.5:
            return "优秀"
        elif avg_score >= 1.0:
            return "正常"
        elif avg_score >= 0.5:
            return "偏低"
        else:
            return "较差"
    
    def find_top_n(
        self, 
        df: pd.DataFrame, 
        metric: str, 
        n: int = 10
    ) -> List[str]:
        """找出Top N的data_id"""
        if metric not in df.columns or 'data_id' not in df.columns:
            return []
        
        sorted_df = df.nlargest(n, metric)
        return sorted_df['data_id'].tolist()
    
    def find_bottom_n(
        self, 
        df: pd.DataFrame, 
        metric: str, 
        n: int = 10
    ) -> List[str]:
        """找出Bottom N的data_id"""
        if metric not in df.columns or 'data_id' not in df.columns:
            return []
        
        sorted_df = df.nsmallest(n, metric)
        return sorted_df['data_id'].tolist()
