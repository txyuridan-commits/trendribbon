# TrendRibbon MVP

绳带、织带及服装辅料 AI 开发工作台。当前版本是可本地运行的 MVP，支持新品开发、客户需求方案、趋势调研、三套概念输出、知识库导入、产品库和历史记录。

## 1. 环境要求
- Python 3.10+
- 建议使用虚拟环境

## 2. 安装与启动

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 Streamlit 显示的本地地址，通常为 http://localhost:8501 。

## 3. 使用方式
1. 打开「新品开发」「客户需求方案」或「趋势调研」。
2. 输入需求，点击「生成 3 套开发方案」。
3. 在每张方案卡片中查看材料、结构、工艺、颜色、配件、卖点、工厂确认项和中英文文案。
4. 点击「保存到产品库」收藏方案。
5. 在「知识库」上传工厂工艺资料（TXT、MD、PDF、DOCX、CSV、JSON）。
6. 在「设置」配置模型 API Key、Base URL 和模型名。未配置 Key 时可使用演示模式。

## 4. AI API 配置
默认兼容 OpenAI Chat Completions 格式：
- Base URL: `https://api.openai.com/v1`
- Model: `gpt-4o-mini`

也可以填写其他兼容服务商提供的 Base URL 和模型名。API Key 保存在本地 `data/settings.json`。请勿把含 Key 的项目目录分享给他人。

## 5. 当前能力边界
- 当前图片能力是生成图像 Prompt，不会直接生成图片文件。
- 知识库为本地关键词检索，不是生产级向量 RAG。
- 数据存储为本地 JSON，适合单机试用，不适合多人并发。
- 不自动推断工厂设备、材料供应、认证、成本、交期或测试结果。
- 所有打样和量产可行性必须由工厂确认。

## 6. 下一阶段建议
1. 接入真实图像生成服务。
2. 使用 embedding + 向量数据库升级 RAG。
3. 增加登录、工厂/租户隔离和云端数据库。
4. 增加 PDF 提案导出、团队协作和方案版本管理。
5. 将趋势研究工作流接入可追溯的外部来源与日期。

## 7. 项目结构
```text
trendribbon_mvp/
├── app.py
├── requirements.txt
├── Dockerfile
├── .gitignore
├── README.md
├── data/
└── knowledge/
```
