from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat_data_service import ChatDataService


class ChatPromptService:
    """对话提示词生成服务"""
    
    BASE_SYSTEM_PROMPT = """你是一个专业的内容账号数据分析助手，擅长帮助用户理解数据分析结果、提供优化建议。

你可以：
1. 回答关于数据分析结果的问题
2. 解释指标含义和趋势
3. 提供内容优化建议
4. 帮助用户理解数据背后的原因

回答要专业、准确、简洁。如果用户询问的数据不在当前上下文中，你可以提示用户或查询相关数据。"""

    ANALYSIS_CONTEXT_PROMPT_TEMPLATE = """
当前对话关联到以下分析任务：
- 分析任务名称：{analysis_name}
- 数据集名称：{dataset_name}
- 分析时间：{created_at}
- 总笔记数：{total_posts}
- 表现分布：
{performance_distribution}

你可以基于这个分析任务的数据回答用户的问题。用户可以询问：
- 表现最好/最差的笔记
- 特定指标的统计
- 按内容类型/发文类型的分析
- 优化建议等

注意：所有数据查询都基于当前关联的分析任务。
"""

    ANALYSIS_RESULT_CONTEXT_PROMPT_TEMPLATE = """
分析结果讨论模式

用户正在查看一篇笔记的AI分析结果，并希望与你讨论或修改建议。

【笔记信息】
- 笔记ID: {data_id}
- 内容形式: {content_type}
- 发文类型: {post_type}
- 款式信息: {style_info}
- 发文链接: {publish_link}

【指标数据】
7天数据：阅读 {read_7d}, 互动 {interact_7d}, 好物访问 {visit_7d}, 好物想要 {want_7d}
14天数据：阅读 {read_14d}, 互动 {interact_14d}, 好物访问 {visit_14d}, 好物想要 {want_14d}

【分析结果】
- 表现评级: {performance}
- 问题指标: {problem_metrics}
- 亮点指标: {highlight_metrics}

【当前AI建议】（用户可能想要修改的内容）
一句话总结：{summary}

优点：
{strengths_text}

问题：
{weaknesses_text}

优化建议：
{suggestions_text}

---

用户可能会：
1. 询问为什么这样建议
2. 要求修改建议，使其更具体或更符合实际情况
3. 对某些建议不满意，希望换个角度
4. 要求补充或删除某些建议

请根据用户的反馈，提供更合适的建议。回答要：
- 理解用户的关切
- 基于数据和笔记内容给出建议
- 保持专业和友好的 tone

【重要】当用户明确要求修改建议时（如"帮我改一下"、"重新写"、"修改建议"等），你需要在回复末尾附上结构化的修改内容，格式如下：

```json:suggestion_update
{{
    "summary": "新的一句话总结（如果需要修改）",
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2", "建议3"]
}}
```

注意：
- 只有用户明确要求修改时才输出这个 JSON 块
- 只包含需要修改的字段，不需要修改的字段可以省略
- JSON 块必须放在回复的最后
- 在 JSON 块之前，先用自然语言解释你的修改思路
"""
    
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.data_service = ChatDataService(db, user_id)
        self.db = db
    
    async def generate_system_prompt(
        self, 
        context_type: str,
        context_analysis_id: Optional[UUID] = None,
        context_analysis_result_id: Optional[UUID] = None
    ) -> str:
        """生成系统提示词"""
        base_prompt = self.BASE_SYSTEM_PROMPT
        
        # 分析结果讨论模式
        if context_type == "analysis_result" and context_analysis_result_id:
            try:
                context = await self.data_service.get_analysis_result_context(context_analysis_result_id)
                
                post_info = context["post_info"]
                analysis_result = context["analysis_result"]
                ai_output = context["current_ai_output"]
                
                # 格式化列表内容
                strengths_text = "\n".join([f"- {s}" for s in (ai_output["strengths"] or [])]) or "无"
                weaknesses_text = "\n".join([f"- {w}" for w in (ai_output["weaknesses"] or [])]) or "无"
                suggestions_text = "\n".join([f"- {s}" for s in (ai_output["suggestions"] or [])]) or "无"
                
                # 获取问题指标和亮点指标
                problem_metrics = analysis_result.get("result_data", {}).get("problem_metrics", [])
                highlight_metrics = analysis_result.get("result_data", {}).get("highlight_metrics", [])
                
                context_prompt = self.ANALYSIS_RESULT_CONTEXT_PROMPT_TEMPLATE.format(
                    data_id=post_info.get("data_id", ""),
                    content_type=post_info.get("content_type", "未知"),
                    post_type=post_info.get("post_type", "未知"),
                    style_info=post_info.get("style_info", "无") or "无",
                    publish_link=post_info.get("publish_link", ""),
                    read_7d=post_info["metrics"].get("read_7d") or 0,
                    interact_7d=post_info["metrics"].get("interact_7d") or 0,
                    visit_7d=post_info["metrics"].get("visit_7d") or 0,
                    want_7d=post_info["metrics"].get("want_7d") or 0,
                    read_14d=post_info["metrics"].get("read_14d") or 0,
                    interact_14d=post_info["metrics"].get("interact_14d") or 0,
                    visit_14d=post_info["metrics"].get("visit_14d") or 0,
                    want_14d=post_info["metrics"].get("want_14d") or 0,
                    performance=analysis_result.get("performance", "未知"),
                    problem_metrics=", ".join(problem_metrics) if problem_metrics else "无",
                    highlight_metrics=", ".join(highlight_metrics) if highlight_metrics else "无",
                    summary=ai_output.get("summary") or "无",
                    strengths_text=strengths_text,
                    weaknesses_text=weaknesses_text,
                    suggestions_text=suggestions_text
                )
                
                return base_prompt + "\n\n" + context_prompt
            except Exception as e:
                print(f"获取分析结果上下文失败: {e}")
                return base_prompt
        
        # 分析任务模式
        elif context_type == "analysis" and context_analysis_id:
            try:
                summary = await self.data_service.get_analysis_summary(context_analysis_id)
                
                performance_dist_text = "\n".join([
                    f"  - {perf}: {count}篇"
                    for perf, count in summary["performance_distribution"].items()
                ])
                
                context_prompt = self.ANALYSIS_CONTEXT_PROMPT_TEMPLATE.format(
                    analysis_name=summary.get("analysis_name", "未命名分析"),
                    dataset_name=summary.get("dataset_name", "未知数据集"),
                    created_at=summary.get("created_at", "未知时间"),
                    total_posts=summary.get("total_posts", 0),
                    performance_distribution=performance_dist_text
                )
                
                return base_prompt + "\n\n" + context_prompt
            except Exception as e:
                print(f"获取分析上下文失败: {e}")
                return base_prompt
        
        return base_prompt


