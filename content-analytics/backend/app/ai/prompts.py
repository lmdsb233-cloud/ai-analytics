"""Prompt模板"""

SYSTEM_PROMPT = """你是一位资深的内容运营分析专家，专门帮助品牌分析笔记表现并优化内容策略。

你的专业领域：
- 视觉呈现分析（构图、色彩、产品展示、场景搭配）
- 标题和文案的吸引力优化
- 用户行为与内容策略洞察
- 数据指标的深度解读

分析原则：
1. 如果提供了图片，必须仔细分析：
   - 产品是否清晰可见、是否为视觉焦点
   - 内容整体效果、色彩搭配协调性
   - 场景选择是否适合目标人群
   - 构图是否符合审美（是否有留白、是否杂乱）
   - 人物状态是否自然有感染力
2. 如果未提供图片和正文，只分析数据，不要编造图文内容
3. 建议必须具体可执行，避免"提高吸引力"这类空话
4. 输出必须严格JSON格式"""

ANALYSIS_PROMPT_TEMPLATE = """请深度分析这篇内容，找出问题并给出可落地的优化方案。

## 笔记基本信息
- 内容形式：{content_type}（图文/视频）
- 发文类型：{post_type}（如：室内穿搭、户外场景、产品展示等）
- 款式/产品：{style_info}

## 笔记内容
**标题**：{content_title}

**正文**：
{content_text}

**配图数量**：{image_count}张

## 数据表现（与同期笔记对比）
- **整体评级**：{performance}
- **表现好的指标**：{highlight_metrics}
- **表现差的指标**：{problem_metrics}
- **具体对比**：{compare_to_avg}

---

请基于以上信息（以及附带的封面图片，如果有的话），输出JSON格式分析：

```json
{{
    "summary": "用1句话概括这篇笔记的核心问题或亮点（限30字）",
    "strengths": [
        "具体优点1（如：标题使用emoji增加点击欲望）",
        "具体优点2"
    ],
    "weaknesses": [
        "具体问题1（如：封面图产品不够突出，被背景抢了视觉焦点）",
        "具体问题2"
    ],
    "suggestions": [
        "具体建议1（如：建议将产品放在画面中心1/3位置，使用纯色背景突出）",
        "具体建议2（如：标题可改为「xxx」，增加搜索关键词覆盖）",
        "具体建议3"
    ]
}}
```

要求：
- strengths/weaknesses 各1-3条，没有就输出空数组
- suggestions 必须3-5条，每条都要具体可执行
- 如果有图片，必须结合图片内容分析
- 不要编造没提供的信息"""

DATA_ONLY_PROMPT_TEMPLATE = """请基于以下数据对这篇内容进行分析，并给出可落地的优化方案。
注意：未提供图文内容，请不要编造标题/正文/画面细节。

## 笔记基本信息
- 内容形式：{content_type}
- 发文类型：{post_type}
- 款式/产品：{style_info}

## 数据表现（与同期笔记对比）
- **整体评级**：{performance}
- **表现好的指标**：{highlight_metrics}
- **表现差的指标**：{problem_metrics}
- **具体对比**：{compare_to_avg}

请输出 JSON 格式分析：
```json
{{
    "summary": "用1句话概括这篇内容的核心问题或亮点（限30字）",
    "strengths": ["具体优点1", "具体优点2"],
    "weaknesses": ["具体问题1", "具体问题2"],
    "suggestions": [
        "具体建议1（可操作）",
        "具体建议2（可操作）",
        "具体建议3（可操作）"
    ]
}}
```

要求：
- strengths/weaknesses 各1-3条，没有就输出空数组
- suggestions 必须3-5条，且要具体可执行
- 不要编造没提供的信息"""


def build_analysis_prompt(input_data: dict) -> str:
    """构建分析Prompt"""
    content_desc = input_data.get('content_description', {})
    analysis_result = input_data.get('analysis_result', {})

    highlight_metrics = analysis_result.get('highlight_metrics', [])
    problem_metrics = analysis_result.get('problem_metrics', [])
    compare_to_avg = analysis_result.get('compare_to_avg', {})

    content_title = content_desc.get('content_title') or ''
    content_text = content_desc.get('content_text') or ''
    if isinstance(content_text, str) and len(content_text) > 500:
        content_text = content_text[:500] + '...'
    cover_image = content_desc.get('cover_image') or ''
    image_urls = content_desc.get('image_urls') or []
    image_count = len(image_urls) if image_urls else (1 if cover_image else 0)

    has_rich_content = bool(content_title.strip() or content_text.strip() or image_count > 0)
    template = ANALYSIS_PROMPT_TEMPLATE if has_rich_content else DATA_ONLY_PROMPT_TEMPLATE

    return template.format(
        content_type=content_desc.get('content_type', '未知'),
        post_type=content_desc.get('post_type', '未知'),
        style_info=content_desc.get('style_info', '无'),
        content_title=content_title or '无',
        content_text=content_text or '无',
        image_count=image_count,
        cover_image=cover_image or '无',
        performance=analysis_result.get('performance', '未知'),
        highlight_metrics='、'.join(highlight_metrics) if highlight_metrics else '无',
        problem_metrics='、'.join(problem_metrics) if problem_metrics else '无',
        compare_to_avg=', '.join([f"{k}: {v}" for k, v in compare_to_avg.items()]) if compare_to_avg else '无数据'
    )
