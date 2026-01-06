# API密钥配置指南

## 📋 配置方式

系统支持通过**前端设置页面**配置API密钥，这是推荐的方式。每个用户可以配置自己的API密钥。

## 🚀 快速开始

### 方式一：通过前端设置页面（推荐）

1. **登录系统**
   - 访问 http://localhost:5173
   - 使用你的账号登录

2. **进入设置页面**
   - 登录后，点击导航栏中的"设置"或访问设置页面

3. **配置API密钥**
   - 选择AI服务提供商（DeepSeek / OpenAI / iFlow）
   - 在对应的输入框中输入API密钥
   - 点击"保存设置"

4. **测试API密钥（可选）**
   - 点击"测试API密钥"按钮验证密钥是否有效

### 方式二：通过API直接配置

如果你熟悉API调用，可以直接使用API配置：

```bash
# 1. 登录获取token
curl -X POST http://localhost:8088/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# 2. 使用返回的token配置API密钥
curl -X PUT http://localhost:8088/api/v1/settings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "ai_provider": "deepseek",
    "deepseek_api_key": "your_deepseek_api_key"
  }'
```

## 🔑 获取API密钥

### DeepSeek
- 访问：https://platform.deepseek.com/
- 注册账号后，在控制台获取API密钥
- 密钥格式：`sk-xxxxxxxxxxxxxxxx`

### OpenAI
- 访问：https://platform.openai.com/
- 注册账号后，在API Keys页面创建密钥
- 密钥格式：`sk-xxxxxxxxxxxxxxxx`

### iFlow
- 访问：https://iflow.cn/
- 注册账号后，在控制台获取API密钥
- 密钥格式：根据iFlow提供的格式

## ✅ 验证配置

配置完成后，你可以：

1. **在设置页面测试**
   - 点击"测试API密钥"按钮
   - 如果显示"API密钥配置正确"，说明配置成功

2. **通过聊天功能测试**
   - 创建一个对话或打开一个分析结果的对话
   - 发送一条消息
   - 如果AI正常回复，说明配置成功

## 🐛 常见问题

### 问题1：提示"未配置API密钥"
- **原因**：还没有配置API密钥或配置的密钥为空
- **解决**：前往设置页面配置API密钥

### 问题2：提示"API密钥配置错误"
- **原因**：输入的API密钥不正确或已过期
- **解决**：检查密钥是否正确，或重新获取新的API密钥

### 问题3：AI服务响应慢或超时
- **原因**：网络问题或API服务繁忙
- **解决**：检查网络连接，稍后重试

## 📝 注意事项

1. **密钥安全**
   - API密钥是敏感信息，请妥善保管
   - 不要在公共场合分享你的API密钥
   - 如果密钥泄露，请立即在服务商平台重新生成

2. **费用说明**
   - 使用AI服务可能会产生费用
   - 请查看各服务商的定价政策
   - 建议设置使用限额，避免意外高额费用

3. **服务商选择**
   - 可以根据需要选择不同的AI服务商
   - 不同服务商的价格、性能、模型能力可能不同
   - 可以在设置中随时切换服务商

## 🔄 更新配置

如果需要更新API密钥：

1. 进入设置页面
2. 在对应的输入框中输入新的API密钥
3. 点击"保存设置"
4. 系统会自动使用新的密钥

## 📞 需要帮助？

如果遇到问题，可以：
- 查看系统日志
- 检查API服务商的服务状态
- 联系技术支持

