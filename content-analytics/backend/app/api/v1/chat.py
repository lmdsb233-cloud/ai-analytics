import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.conversation import Conversation, ConversationMessage
from app.models.analysis import Analysis, AnalysisResult
from app.schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    ConversationMessageCreate, ConversationMessageResponse
)
from app.schemas.common import ResponseModel
from app.ai.factory import get_ai_provider
from app.services.chat_prompt_service import ChatPromptService
from app.core.config import settings

router = APIRouter()


@router.post("/conversations", response_model=ResponseModel[ConversationResponse])
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新对话"""
    # 如果是分析结果对话，验证权限
    if data.context_type == "analysis_result" and data.context_analysis_result_id:
        result = await db.execute(
            select(AnalysisResult)
            .join(AnalysisResult.analysis)
            .where(
                AnalysisResult.id == data.context_analysis_result_id,
                Analysis.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析结果不存在或无权限"
            )
        
        # 自动生成标题（基于笔记信息）
        from app.models.post import Post
        result_data = await db.execute(
            select(AnalysisResult, Post)
            .join(Post, AnalysisResult.post_id == Post.id)
            .where(AnalysisResult.id == data.context_analysis_result_id)
        )
        row = result_data.first()
        if row:
            post = row[1]
            data.title = data.title or f"讨论：{post.data_id}的分析建议"
    
    # 如果是分析任务对话，验证权限
    elif data.context_type == "analysis" and data.context_analysis_id:
        result = await db.execute(
            select(Analysis).where(
                Analysis.id == data.context_analysis_id,
                Analysis.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在或无权限"
            )
    
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title or "新对话",
        context_type=data.context_type,
        context_analysis_id=data.context_analysis_id,
        context_analysis_result_id=data.context_analysis_result_id
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ResponseModel(data=ConversationResponse.from_orm(conversation))


@router.get("/conversations", response_model=ResponseModel[List[ConversationResponse]])
async def get_conversations(
    context_type: Optional[str] = None,
    context_analysis_id: Optional[uuid.UUID] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话列表"""
    query = select(Conversation).where(Conversation.user_id == current_user.id)
    
    if context_type:
        query = query.where(Conversation.context_type == context_type)
    if context_analysis_id:
        query = query.where(Conversation.context_analysis_id == context_analysis_id)
    
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    conversations = result.scalars().all()
    
    # 获取消息数量
    response_data = []
    for conv in conversations:
        msg_count_result = await db.execute(
            select(func.count(ConversationMessage.id))
            .where(ConversationMessage.conversation_id == conv.id)
        )
        msg_count = msg_count_result.scalar_one()
        
        conv_dict = ConversationResponse.from_orm(conv).dict()
        conv_dict["message_count"] = msg_count
        response_data.append(conv_dict)
    
    return ResponseModel(data=response_data)


@router.get("/conversations/{conversation_id}", response_model=ResponseModel[ConversationDetailResponse])
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话详情（包含消息历史）"""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    messages = [
        ConversationMessageResponse.from_orm(msg) 
        for msg in conversation.messages
    ]
    
    conv_dict = ConversationResponse.from_orm(conversation).dict()
    conv_dict["messages"] = [msg.dict() for msg in messages]
    conv_dict["message_count"] = len(messages)
    
    return ResponseModel(data=conv_dict)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    message_in: ConversationMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息并返回SSE流式响应"""
    # 验证对话权限
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 保存用户消息
    user_message = ConversationMessage(
        conversation_id=conversation_id,
        role="user",
        content=message_in.content
    )
    db.add(user_message)
    await db.commit()
    
    # 获取对话历史（包含刚保存的用户消息）
    await db.refresh(conversation)
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one()
    
    messages_history = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
        if msg.role in ["user", "assistant"]
    ]
    
    # 生成系统提示词
    prompt_service = ChatPromptService(db, current_user.id)
    system_prompt = await prompt_service.generate_system_prompt(
        context_type=conversation.context_type,
        context_analysis_id=conversation.context_analysis_id,
        context_analysis_result_id=conversation.context_analysis_result_id
    )
    
    # 获取用户设置和API密钥
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = settings_result.scalar_one_or_none()
    if not user_settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在设置中配置AI服务"
        )
    
    api_key = user_settings.get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请先配置{user_settings.ai_provider}的API密钥"
        )
    
    # 获取 AI Provider
    ai_provider = get_ai_provider(
        provider_name=user_settings.ai_provider,
        api_key=api_key
    )
    
    # 保存需要在生成器中使用的变量
    conv_id = conversation_id
    provider_model_name = ai_provider.model_name
    
    # 复制需要的变量，避免闭包问题
    _messages_history = list(messages_history)
    _system_prompt = system_prompt
    _ai_provider = ai_provider
    
    async def generate_response():
        full_response = ""
        
        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            print(f"[DEBUG] Starting chat_stream")
            print(f"[DEBUG] Messages count: {len(_messages_history)}")
            print(f"[DEBUG] Provider: {provider_model_name}")
            
            chunk_count = 0
            async for chunk in _ai_provider.chat_stream(
                messages=_messages_history,
                system_prompt=_system_prompt,
                temperature=0.7,
                max_tokens=2000
            ):
                chunk_count += 1
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            print(f"[DEBUG] Received {chunk_count} chunks, total length: {len(full_response)}")
            
            # 在生成器中创建新的数据库会话来保存响应
            from app.db.session import async_session_maker
            async with async_session_maker() as save_db:
                assistant_message = ConversationMessage(
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_response,
                    model_name=provider_model_name,
                    tokens_used=None,
                    extra_data=None
                )
                save_db.add(assistant_message)
                
                # 更新对话时间
                await save_db.execute(
                    update(Conversation)
                    .where(Conversation.id == conv_id)
                    .values(updated_at=datetime.utcnow())
                )
                
                await save_db.commit()
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"生成响应失败: {error_msg}")
            print(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/analysis-results/{analysis_result_id}/conversation", response_model=ResponseModel[ConversationResponse])
async def create_conversation_from_analysis_result(
    analysis_result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从分析结果创建对话（便捷接口）
    
    在笔记详情页点击"与AI讨论"时调用
    """
    from app.models.post import Post
    
    # 验证分析结果存在且属于当前用户
    result = await db.execute(
        select(AnalysisResult, Post)
        .join(Post, AnalysisResult.post_id == Post.id)
        .join(AnalysisResult.analysis)
        .where(
            AnalysisResult.id == analysis_result_id,
            Analysis.user_id == current_user.id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在或无权限"
        )
    
    analysis_result, post = row
    
    # 检查是否已存在对话（1小时内）
    existing = await db.execute(
        select(Conversation).where(
            Conversation.context_type == "analysis_result",
            Conversation.context_analysis_result_id == analysis_result_id,
            Conversation.user_id == current_user.id
        ).order_by(Conversation.updated_at.desc()).limit(1)
    )
    existing_conv = existing.scalars().first()
    
    # 如果存在且是最近创建的（比如1小时内），返回现有对话
    if existing_conv:
        from datetime import timedelta
        if existing_conv.created_at > datetime.utcnow() - timedelta(hours=1):
            return ResponseModel(data=ConversationResponse.from_orm(existing_conv))
    
    # 创建新对话
    conversation = Conversation(
        user_id=current_user.id,
        title=f"讨论：{post.data_id}的分析建议",
        context_type="analysis_result",
        context_analysis_result_id=analysis_result_id
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ResponseModel(data=ConversationResponse.from_orm(conversation))


@router.get("/analysis-results/{analysis_result_id}/context", response_model=ResponseModel[dict])
async def get_analysis_result_context(
    analysis_result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分析结果的上下文信息（用于前端应用修改）"""
    from app.models.post import Post
    
    # 使用 selectinload 而不是 join，避免多行问题
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.analysis))
        .where(AnalysisResult.id == analysis_result_id)
    )
    analysis_result = result.scalars().first()
    
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    # 验证权限
    if analysis_result.analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此分析结果"
        )
    
    return ResponseModel(data={
        "analysis_result_id": str(analysis_result_id),
        "post_id": str(analysis_result.post_id),
        "analysis_id": str(analysis_result.analysis_id)
    })
