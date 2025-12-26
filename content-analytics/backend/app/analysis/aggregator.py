import pandas as pd
from typing import Dict, List, Any
from .processor import DataProcessor
from .calculator import MetricsCalculator
from .anomaly import AnomalyDetector


class AnalysisAggregator:
    """分析聚合器 - 整合所有分析模块"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.processor = DataProcessor(df)
        self.processed_df = None
        self.calculator = None
        self.detector = None
        self.stats = None
    
    def prepare(self) -> 'AnalysisAggregator':
        """准备数据"""
        self.processed_df = self.processor.process()
        self.calculator = MetricsCalculator(self.processed_df)
        self.stats = self.calculator.calculate_basic_stats()
        self.detector = AnomalyDetector(self.stats)
        return self
    
    def analyze_single_post(self, row: pd.Series) -> Dict[str, Any]:
        """分析单篇笔记"""
        # 检测异常
        anomalies = self.detector.detect_anomalies(row)
        
        # 判断整体表现
        performance = self.detector.determine_performance(row)
        
        # 与均值比较
        compare_to_avg = self.calculator.compare_to_baseline(row, 'mean')
        
        # 百分位排名
        percentile_ranks = self.calculator.get_percentile_rank(row)
        
        return {
            'performance': performance,
            'problem_metrics': anomalies['problem_metrics'],
            'highlight_metrics': anomalies['highlight_metrics'],
            'compare_to_avg': compare_to_avg,
            'percentile_ranks': percentile_ranks
        }
    
    def analyze_all(self) -> List[Dict[str, Any]]:
        """分析所有笔记"""
        if self.processed_df is None:
            self.prepare()
        
        results = []
        for idx, row in self.processed_df.iterrows():
            result = self.analyze_single_post(row)
            result['data_id'] = row.get('data_id')
            result['row_index'] = idx
            results.append(result)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取汇总信息"""
        if self.processed_df is None:
            self.prepare()
        
        # 按内容类型分组统计
        group_stats = self.calculator.calculate_group_stats('content_type')
        
        # 按发文类型分组统计
        post_type_stats = self.calculator.calculate_group_stats('post_type')
        
        return {
            'total_posts': len(self.processed_df),
            'overall_stats': self.stats,
            'content_type_stats': group_stats,
            'post_type_stats': post_type_stats
        }
    
    def get_ai_input_for_post(self, row: pd.Series, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成给AI的输入数据"""
        return {
            'content_description': {
                'content_type': row.get('content_type', ''),
                'post_type': row.get('post_type', ''),
                'style_info': row.get('style_info', '')
            },
            'analysis_result': {
                'performance': analysis_result['performance'],
                'problem_metrics': analysis_result['problem_metrics'],
                'highlight_metrics': analysis_result['highlight_metrics'],
                'compare_to_avg': analysis_result['compare_to_avg']
            }
        }
