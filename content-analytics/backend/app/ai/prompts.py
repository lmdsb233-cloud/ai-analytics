"""Prompt模板"""

SYSTEM_PROMPT = """你是一个专业的内容运营分析师，擅长分析社交媒体笔记的表现数据并给出优化建议。
你需要根据提供的数据分析结果，给出专业、具体、可执行的建议。

输出要求：
1. 必须严格按照JSON格式输出
2. 建议要具体、可执行，不要泛泛而谈
3. 结合内容类型和发文类型给出针对性建议
4. 语言简洁专业"""

ANALYSIS_PROMPT_TEMPLATE = """请分析以下笔记的表现数据，并给出优化建议。

## 笔记信息
- 内容形式：{content_type}
- 发文类型：{post_type}
- 款式信息：{style_info}

## 数据分析结果
- 整体表现：{performance}
- 表现突出的指标：{highlight_metrics}
- 表现较差的指标：{problem_metrics}
- 与平均值对比：{compare_to_avg}

请严格按照以下JSON格式输出分析结果：

```json
{{
    "summary": "一句话总结这篇笔记的表现",
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2", "建议3"]
}}
```

注意：
1. summary限制在50字以内
2. strengths和weaknesses各列出1-3条
3. suggestions列出3-5条具体可执行的优化建议
4. 如果某项为空，输出空数组[]"""


def build_analysis_prompt(input_data: dict) -> str:
    """构建分析Prompt"""
    content_desc = input_data.get('content_description', {})
    analysis_result = input_data.get('analysis_result', {})
    
    highlight_metrics = analysis_result.get('highlight_metrics', [])
    problem_metrics = analysis_result.get('problem_metrics', [])
    compare_to_avg = analysis_result.get('compare_to_avg', {})
    
    return ANALYSIS_PROMPT_TEMPLATE.format(
        content_type=content_desc.get('content_type', '未知'),
        post_type=content_desc.get('post_type', '未知'),
        style_info=content_desc.get('style_info', '无'),
        performance=analysis_result.get('performance', '未知'),
        highlight_metrics='、'.join(highlight_metrics) if highlight_metrics else '无',
        problem_metrics='、'.join(problem_metrics) if problem_metrics else '无',
        compare_to_avg=', '.join([f"{k}: {v}" for k, v in compare_to_avg.items()]) if compare_to_avg else '无数据'
    )
