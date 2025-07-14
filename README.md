# 行政案件数据库系统v3.0

## 项目简介
本项目基于Flask实现Web应用，支持多文件（PDF、Word、TXT等）上传，自动调用本地Dify工作流进行智能解析与结构化信息抽取，适用于合同、诉讼案件等文档的批量处理与数据库录入。

## 主要功能
- 支持多种文件格式（PDF、Word、TXT、图片等）批量上传
- 自动对接本地Dify工作流，智能解析文件内容
- 结构化提取案件、合同等关键信息
- **流式SSE体验**：Dify工作流结果实时流式推送，前端边处理边展示，极致交互体验
- **现代苹果风前端**：简洁大方、圆角卡片、蓝色渐变按钮、响应式设计

## 安装与运行
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动Flask服务：
   ```bash
   python app.py
   ```
3. 访问前端页面：
   浏览器打开 http://localhost:8888

## API说明
- `POST /upload`
  - 参数：
    - `input_data`：多文件上传字段，支持PDF、Word、TXT等
  - 返回：Dify工作流结构化处理结果（SSE流式，event-stream）

## 前后端流式交互说明
- 前端页面支持多文件选择与上传，上传后自动通过SSE流式展示Dify返回的结构化结果。
- 仅展示最终workflow_finished事件的task_id、status和output三项内容，避免中间过程干扰。
- 文件字段名需与Dify工作流Start节点变量名一致（本项目为`input_data`）。
- 前端采用现代苹果风格UI，极简美观。

## Dify对接说明
- 本地Dify服务API地址：`http://localhost/v1`
- 工作流ID：`C3DkottL68M7X1Ic`
- API Key：`app-Nfqyj2jlcOMxNKFhOnekv9tr`
- Flask后端通过`/v1/workflows/run`接口与Dify对接，采用`multipart/form-data`格式上传文件，workflow调用为SSE流式（streaming模式）。
- 需保证Dify工作流Start节点变量名为`input_data`，类型为`file-list`。

## 目录结构
```
├── app.py           # Flask主程序
├── requirements.txt # 依赖
├── README.md        # 项目说明
├── templates/
│   └── index.html   # 前端页面（苹果风美化+流式体验）
└── static/
    └── style.css    # 样式（可选）
```

## 参考
- [Dify官方文档](https://docs.dify.ai/)
- [Dify工作流文件上传说明](https://docs.dify.ai/guides/workflow/file-upload) 