"""导出任务"""
import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from app.tasks.celery_app import celery_app
from app.db.session import async_session_maker, create_thread_session_maker
from app.models.export import Export, ExportStatus, ExportFormat
from app.models.analysis import Analysis, AnalysisResult, AIOutput
from app.core.config import settings


def run_async(coro):
    """在同步环境中运行异步代码"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="run_export_task")
def run_export_task(self, export_id: str):
    """Celery导出任务入口"""
    return run_async(_run_export(export_id, use_thread_session=True))


async def _run_export(export_id: str, use_thread_session: bool = False):
    """执行导出任务"""
    if use_thread_session:
        session_maker, thread_engine = create_thread_session_maker()
    else:
        session_maker = async_session_maker
        thread_engine = None

    try:
        async with session_maker() as db:
            # 获取导出记录
            result = await db.execute(
                select(Export).where(Export.id == uuid.UUID(export_id))
            )
            export = result.scalar_one_or_none()
            
            if not export:
                return {"error": "导出记录不存在"}
            
            # 更新状态为处理中
            export.status = ExportStatus.PROCESSING
            await db.commit()
            
            try:
                # 获取分析数据
                result = await db.execute(
                    select(Analysis)
                    .options(selectinload(Analysis.dataset))
                    .where(Analysis.id == export.analysis_id)
                )
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    raise Exception("分析任务不存在")
                
                # 获取分析结果
                results = await db.execute(
                    select(AnalysisResult)
                    .options(
                        selectinload(AnalysisResult.post),
                        selectinload(AnalysisResult.ai_output)
                    )
                    .where(AnalysisResult.analysis_id == analysis.id)
                    .order_by(AnalysisResult.created_at)
                )
                analysis_results = results.scalars().all()
                
                # 根据格式导出
                if export.format == ExportFormat.EXCEL:
                    file_path = await _export_to_excel(analysis, analysis_results, export_id)
                elif export.format == ExportFormat.JSON:
                    file_path = await _export_to_json(analysis, analysis_results, export_id)
                else:
                    raise Exception(f"暂不支持 {export.format.value} 格式导出")
                
                # 更新导出记录
                export.file_path = file_path
                export.status = ExportStatus.COMPLETED
                export.completed_at = datetime.utcnow()
                await db.commit()
                
                return {"success": True, "file_path": file_path}
                
            except Exception as e:
                export.status = ExportStatus.FAILED
                export.error_message = str(e)[:1000]
                await db.commit()
                return {"error": str(e)}
    finally:
        if thread_engine:
            await thread_engine.dispose()


async def _export_to_excel(analysis: Analysis, results: list, export_id: str) -> str:
    """导出为Excel格式"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "分析报告"
    
    # 样式定义
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="FF2442", end_color="FF2442", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    cell_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 写入标题行
    headers = [
        "序号",
        "笔记ID",
        "内容形式",
        "发文类型",
        "素材来源",
        "款式信息",
        "发布时间",
        "7天阅读/播放",
        "7天互动",
        "7天好物访问",
        "7天好物想要",
        "14天阅读/播放",
        "14天互动",
        "14天好物访问",
        "14天好物想要",
        "表现",
        "问题指标",
        "亮点指标",
        "对比均值",
        "AI总结",
        "优势",
        "不足",
        "优化建议"
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # 写入数据
    for row_idx, ar in enumerate(results, 2):
        # 基础数据
        post = getattr(ar, "post", None)
        result_data = ar.result_data or {}
        compare_to_avg = result_data.get("compare_to_avg") or {}
        compare_text = "；".join([f"{k}:{v}" for k, v in compare_to_avg.items()]) if isinstance(compare_to_avg, dict) else ""
        problem_metrics = result_data.get("problem_metrics") or []
        highlight_metrics = result_data.get("highlight_metrics") or []

        ws.cell(row=row_idx, column=1, value=row_idx - 1).border = thin_border
        ws.cell(row=row_idx, column=2, value=(post.data_id if post else "")).border = thin_border
        ws.cell(row=row_idx, column=3, value=(post.content_type if post else "")).border = thin_border
        ws.cell(row=row_idx, column=4, value=(post.post_type if post else "")).border = thin_border
        ws.cell(row=row_idx, column=5, value=(post.source if post else "")).border = thin_border
        ws.cell(row=row_idx, column=6, value=(post.style_info if post else "")).border = thin_border
        ws.cell(row=row_idx, column=7, value=(str(post.publish_time) if post and post.publish_time else "")).border = thin_border
        
        # 数据指标
        ws.cell(row=row_idx, column=8, value=(post.read_7d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=9, value=(post.interact_7d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=10, value=(post.visit_7d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=11, value=(post.want_7d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=12, value=(post.read_14d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=13, value=(post.interact_14d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=14, value=(post.visit_14d if post else None)).border = thin_border
        ws.cell(row=row_idx, column=15, value=(post.want_14d if post else None)).border = thin_border

        # 计算指标
        ws.cell(row=row_idx, column=16, value=(ar.performance or "")).border = thin_border
        ws.cell(row=row_idx, column=17, value=("、".join(problem_metrics) if isinstance(problem_metrics, list) else "")).border = thin_border
        ws.cell(row=row_idx, column=18, value=("、".join(highlight_metrics) if isinstance(highlight_metrics, list) else "")).border = thin_border
        ws.cell(row=row_idx, column=19, value=compare_text).border = thin_border
        
        # AI分析结果
        if ar.ai_output:
            ws.cell(row=row_idx, column=20, value=ar.ai_output.summary or "").border = thin_border
            ws.cell(row=row_idx, column=21, value="\n".join(ar.ai_output.strengths or [])).border = thin_border
            ws.cell(row=row_idx, column=22, value="\n".join(ar.ai_output.weaknesses or [])).border = thin_border
            ws.cell(row=row_idx, column=23, value="\n".join(ar.ai_output.suggestions or [])).border = thin_border
        else:
            for col in range(20, 24):
                ws.cell(row=row_idx, column=col, value="未分析").border = thin_border
        
        # 设置对齐方式
        for col in range(1, 24):
            ws.cell(row=row_idx, column=col).alignment = cell_alignment
    
    # 设置列宽
    column_widths = [6, 14, 10, 10, 10, 20, 18, 12, 12, 12, 12, 12, 12, 12, 12, 8, 18, 18, 24, 30, 24, 24, 30]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width
    
    # 冻结首行
    ws.freeze_panes = "A2"
    
    # 保存文件
    export_dir = os.path.join(settings.UPLOAD_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    filename = f"analysis_report_{export_id}.xlsx"
    file_path = os.path.join(export_dir, filename)
    wb.save(file_path)
    
    return file_path


async def _export_to_json(analysis: Analysis, results: list, export_id: str) -> str:
    """导出为JSON格式"""
    import json
    
    data = {
        "analysis": {
            "id": str(analysis.id),
            "name": analysis.name,
            "created_at": str(analysis.created_at),
            "status": analysis.status.value
        },
        "results": []
    }
    
    for ar in results:
        post = getattr(ar, "post", None)
        item = {
            "analysis_result": {
                "id": str(ar.id),
                "performance": ar.performance,
                "result_data": ar.result_data,
                "created_at": str(ar.created_at)
            },
            "post": {
                "id": str(post.id) if post else None,
                "data_id": post.data_id if post else None,
                "publish_time": str(post.publish_time) if post and post.publish_time else None,
                "publish_link": post.publish_link if post else None,
                "content_type": post.content_type if post else None,
                "post_type": post.post_type if post else None,
                "source": post.source if post else None,
                "style_info": post.style_info if post else None,
                "metrics": {
                    "read_7d": post.read_7d if post else None,
                    "interact_7d": post.interact_7d if post else None,
                    "visit_7d": post.visit_7d if post else None,
                    "want_7d": post.want_7d if post else None,
                    "read_14d": post.read_14d if post else None,
                    "interact_14d": post.interact_14d if post else None,
                    "visit_14d": post.visit_14d if post else None,
                    "want_14d": post.want_14d if post else None
                }
            },
            "ai_analysis": None
        }

        if ar.ai_output:
            item["ai_analysis"] = {
                "summary": ar.ai_output.summary,
                "strengths": ar.ai_output.strengths,
                "weaknesses": ar.ai_output.weaknesses,
                "suggestions": ar.ai_output.suggestions,
                "model_name": ar.ai_output.model_name,
                "created_at": str(ar.ai_output.created_at)
            }

        data["results"].append(item)
    
    # 保存文件
    export_dir = os.path.join(settings.UPLOAD_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    filename = f"analysis_report_{export_id}.json"
    file_path = os.path.join(export_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return file_path
