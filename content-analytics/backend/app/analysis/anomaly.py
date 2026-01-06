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
        """检测单行数据的异常
        
        使用分位数判断（更合理）：
        - 亮点：高于75分位数，且Q75>0
        - 问题：低于25分位数，或者值=0但中位数>0（说明大部分都有值，0是异常差）
        """
        highlights = []  # 表现突出的指标
        problems = []    # 表现较差的指标
        
        for metric, stat in self.stats.items():
            if metric not in row or pd.isna(row[metric]):
                continue
            
            value = row[metric]
            median = stat.get('median', 0)
            q75 = stat.get('q75', median)
            q25 = stat.get('q25', median)
            
            metric_name = self.METRIC_NAMES.get(metric, metric)
            
            # 高于75分位数为亮点
            if value > q75 and q75 > 0:
                highlights.append(metric_name)
            # 低于25分位数为问题
            elif value < q25 and median >= 1:
                problems.append(metric_name)
            # 特殊情况：值=0但中位数>0，说明0是异常差的表现
            elif value == 0 and median > 0:
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
        """判断整体表现
        
        综合考虑阅读、互动、转化指标
        """
        if primary_metrics is None:
            # 综合考虑 7 天 + 14 天指标，按重要性加权
            primary_metrics = [
                ('read_7d', 1.0),
                ('read_14d', 1.0),
                ('interact_7d', 1.0),
                ('interact_14d', 1.0),
                ('visit_7d', 0.8),
                ('visit_14d', 0.8),
                ('want_7d', 0.8),
                ('want_14d', 0.8),
            ]
        
        weighted_scores = []
        total_weight = 0
        
        for metric_info in primary_metrics:
            if isinstance(metric_info, tuple):
                metric, weight = metric_info
            else:
                metric, weight = metric_info, 1.0
                
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
            weighted_scores.append(ratio * weight)
            total_weight += weight
        
        if not weighted_scores or total_weight == 0:
            return "正常"
        
        avg_score = sum(weighted_scores) / total_weight
        
        if avg_score >= 1.3:
            return "优秀"
        elif avg_score >= 0.9:
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
