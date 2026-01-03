# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供项目指导。

## 项目概述

Auto-Arxiv-Subscription 是一个自动化的 ArXiv 论文通知系统，每天通过邮件发送匹配指定关键词的论文。系统运行在 GitHub Actions 上，无需服务器支持。

### 系统工作流程

1. 从 ArXiv RSS 订阅源获取今日论文（cs.AI, cs.CV, cs.CG, cs.CL, stat.ML）
2. 将每日论文记录保存到 `papers/YYYY-MM-DD.yaml` 用于去重
3. 过滤掉前一天已发送的论文
4. 根据用户定义的关键词过滤论文（不区分大小写的标题匹配）
5. 可选的 AI 增强（使用 DashScope API）：
   - 摘要中文翻译
   - 关键词提取
   - 主要贡献总结
   - **与目标领域的关联度评分（1-5分）**
6. 通过 SMTP 发送格式化的 HTML 邮件
7. 自动将新的 YAML 文件提交到仓库

## 环境配置

### 必需的环境变量

在 GitHub Secrets（Settings → Secrets → Actions）或本地 `.env` 文件中配置：

- `EMAIL` - 发件人邮箱（推荐 QQ 邮箱）
- `EMAIL_TOKEN` - 邮箱授权码/应用密码
- `RECEIVER_EMAIL` - 收件人邮箱地址
- `KEYWORDS` - 搜索关键词，空格分隔（例如："3D BEV occupancy detection"）
- `DOMAIN` - 目标领域名称（默认："自动驾驶"，用于关联度评分）
- `DASHSCOPE_API_KEY` - 阿里云 DashScope API 密钥
- `OPENAI_MODEL` - AI 模型（默认："qwen3-max-preview"）

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 直接运行（带命令行参数）
python src/main.py \
  --email YOUR_EMAIL \
  --token YOUR_TOKEN \
  --receiver RECEIVER_EMAIL \
  --keywords keyword1 keyword2 \
  --domain "自动驾驶"

# 或使用 .env 文件
export EMAIL="your@email.com"
export EMAIL_TOKEN="your_token"
export RECEIVER_EMAIL="receiver@email.com"
export KEYWORDS="3D detection BEV"
export DOMAIN="自动驾驶"
export DASHSCOPE_API_KEY="your_api_key"
python src/main.py \
  --email $EMAIL \
  --token $EMAIL_TOKEN \
  --receiver $RECEIVER_EMAIL \
  --keywords $KEYWORDS \
  --domain "$DOMAIN"
```

### 依赖说明

- **requests** - HTTP 库，用于获取 RSS 订阅源
- **beautifulsoup4** & **lxml** - HTML/XML 解析
- **openai** - DashScope API 客户端
- **pyyaml** - YAML 文件读写，用于论文去重记录

## 项目架构

### 模块化结构

项目采用模块化设计，代码按功能组织：

```
src/
├── main.py                 # 主程序入口（工作流程编排）
├── arxiv/                  # ArXiv 数据获取模块
│   ├── __init__.py
│   └── fetcher.py         # RSS 获取和关键词过滤
├── ai/                     # AI 处理模块
│   ├── __init__.py
│   └── processor.py       # DashScope API 调用
├── mailer/                 # 邮件发送模块
│   ├── __init__.py
│   └── sender.py          # HTML 生成和 SMTP 发送
└── utils/                  # 工具模块
    ├── __init__.py
    └── deduplication.py   # YAML 去重功能
```

### 核心模块说明

#### `src/main.py` - 主程序（约 100 行）
**职责**：工作流程编排和模块调用协调
- 参数解析（argparse）
- 初始化 AI 客户端
- 调用各模块完成完整工作流
- 不包含具体业务逻辑实现

**关键函数**：
- `main(args)` - 主工作流程

#### `src/arxiv/fetcher.py` - ArXiv 数据获取（约 120 行）
**职责**：从 ArXiv RSS 获取论文并进行关键词过滤

**导出函数**：
- `get_arxiv_data()` - 获取今日论文
  - 从 5 个 RSS 订阅源获取数据
  - 解析日期，只保留今天发布的论文
  - 返回：`{title: (link, abstract)}` 字典

- `filter_keywords(papers_dict, keywords)` - 关键词过滤
  - 不区分大小写的标题子串匹配
  - 返回：`{keyword: [(title, link, abstract), ...]}` 字典

**RSS 订阅源配置**：
```python
RSS_FEEDS = {
    "AI": "cs.AI",
    "CV": "cs.CV",
    "CG": "cs.CG",
    "CL": "cs.CL",
    "ML": "stat.ML"
}
```

#### `src/ai/processor.py` - AI 处理（约 180 行）
**职责**：使用 DashScope API 处理论文摘要

**导出函数**：
- `init_ai_client()` - 初始化 AI 客户端
  - 使用环境变量 `DASHSCOPE_API_KEY`
  - 返回 OpenAI 兼容客户端实例

- `process_abstract_with_ai(client, title, abstract, domain)` - 处理单篇论文
  - 翻译摘要为中文
  - 提取 3-5 个关键词
  - 总结主要贡献
  - **评估与目标领域的关联度（1-5 分）**
  - 返回：`(chinese_abstract, main_contribution, keywords, relevance_score)`

- `process_papers_with_ai(filtered_papers, ai_client, domain)` - 批量处理
  - 遍历所有论文并调用 AI 处理
  - API 调用间隔 5 秒（避免限流）
  - 返回处理后的论文字典

**AI Prompt 关键要素**：
- 目标领域（domain 参数）
- 4 个任务：翻译、关键词、贡献、关联度评分
- JSON 格式返回

#### `src/mailer/sender.py` - 邮件发送（约 350 行）
**职责**：生成 HTML 邮件并发送

**导出函数**：
- `generate_email_html(processed_papers, ai_client, domain)` - 生成 HTML 内容
  - 8 种预定义颜色方案轮换
  - 响应式 CSS 样式
  - 关联度评分徽章和星级显示
  - 领域推荐横幅（渐变色背景）

- `sendEmail(msg_from, msg_to, auth_id, title, content)` - 发送邮件
  - 使用 QQ 邮箱 SMTP（smtp.qq.com:465）
  - 支持 HTML 格式

**颜色方案**（8 种）：
1. 红色系 (#FF6B6B)
2. 青色系 (#4ECDC4)
3. 蓝色系 (#45B7D1)
4. 绿色系 (#96CEB4)
5. 黄色系 (#FECA57)
6. 紫色系 (#A29BFE)
7. 粉色系 (#FD79A8)
8. 靛蓝系 (#778BEB)

**关联度评分样式**：
- 5 分（非常相关）- 绿色徽章 + ★★★★★
- 4 分（相关）- 蓝色徽章 + ★★★★☆
- 3 分（一般）- 橙色徽章 + ★★★☆☆
- 2 分（不太相关）- 红色徽章 + ★★☆☆☆
- 1 分（不相关）- 灰色徽章 + ★☆☆☆☆

#### `src/utils/deduplication.py` - 去重工具（约 60 行）
**职责**：管理论文去重记录

**导出函数**：
- `save_today_papers(papers_dict)` - 保存今日论文
  - 创建 `papers/` 目录（如不存在）
  - 保存为 `papers/YYYY-MM-DD.yaml`
  - 格式：`{date, total_count, papers: [titles]}`

- `load_previous_papers()` - 加载前一天的论文
  - 读取 `papers/YYYY-MM-DD.yaml`（昨天的日期）
  - 返回论文标题集合（set）

### 数据流

1. **RSS 订阅源** → BeautifulSoup 解析 → 提取今日论文（标题、链接、摘要）
2. **保存记录** → `papers/YYYY-MM-DD.yaml`
3. **加载前一日记录** → 移除重复论文
4. **关键词过滤** → 按匹配的关键词分组
5. **AI 处理**（可选）→ 5 秒延迟间隔
6. **生成 HTML 邮件** → SMTP 发送
7. **GitHub Actions** → 自动提交 YAML 文件到仓库

### GitHub Actions 工作流

**配置文件**：`.github/workflows/actions.yml`

**触发条件**：
- 推送到 main 分支
- 定时任务（UTC 23:00 / CST 7:00）
- 手动触发（watch 事件）

**运行环境**：
- ubuntu-latest
- Python 3.10

**依赖安装**：
```bash
python -m pip install --upgrade requests lxml bs4 openai pyyaml
```

**环境变量传递**：
```yaml
env:
  EMAIL: ${{ secrets.EMAIL }}
  EMAIL_TOKEN: ${{ secrets.EMAIL_TOKEN }}
  RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}
  KEYWORDS: ${{ secrets.KEYWORDS }}
  DOMAIN: ${{ secrets.DOMAIN }}
  DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
  OPENAI_MODEL: ${{ secrets.OPENAI_MODEL }}
```

**自动提交**：
- 每次运行后自动提交 `papers/` 目录
- 维护去重历史记录

## 重要约束

- **仅处理今日论文**（通过 RSS 的 pubDate 判断）
- **与前一日论文去重** - 跳过昨天已发送的论文
- **关键词匹配**：不区分大小写，仅匹配论文标题（子串匹配）
- **AI 处理限制**：每次调用间隔 5 秒，避免速率限制
- **邮件格式**：HTML 格式，内嵌 CSS
- **SMTP 配置**：使用 QQ 邮箱（可修改为其他提供商）
- **容错机制**：AI 处理失败时回退到原始英文摘要

## 论文去重机制

系统维护已发送论文的历史记录，避免重复通知：

### 存储结构
```
papers/
  ├── 2026-01-01.yaml
  ├── 2026-01-02.yaml
  └── 2026-01-03.yaml
```

### YAML 文件格式
```yaml
date: 2026-01-03
total_count: 42
papers:
  - Deep Learning for 3D Vision: A Survey
  - Attention Is All You Need
  - ...
```

### 去重逻辑
1. 每天将所有获取的论文保存到 `papers/YYYY-MM-DD.yaml`
2. 关键词过滤前，加载前一天的 YAML 文件
3. 排除与前一天标题匹配的论文
4. 只有新论文进入关键词过滤和邮件生成流程
5. GitHub Actions 每次运行后自动提交新的 YAML 文件

这样可以确保在多天仍出现在今日 RSS 订阅源中的论文只发送一次。

## 关联度评分功能

### 评分标准（1-5 分）

- **5 分（非常相关）**：论文直接研究目标领域，高度相关
- **4 分（相关）**：论文内容与目标领域密切相关
- **3 分（一般）**：论文与目标领域有一定关联
- **2 分（不太相关）**：论文与目标领域关联较弱
- **1 分（不相关）**：论文与目标领域基本无关

### AI 评分依据

AI 根据以下因素评估关联度：
- 论文标题与目标领域的关键词匹配
- 摘要内容的主题相关性
- 技术方法和应用场景的关联程度
- 研究领域和目标领域的重叠度

### 邮件中的展示

每篇论文显示：
1. **关联度徽章**：彩色徽章显示评级文字（如"非常相关"）
2. **星级评分**：★ 和 ☆ 组合显示（如 ★★★★★）
3. **AI 增强标签**：显示该论文经过 AI 处理

### 邮件头部横幅

当 AI 功能启用时，邮件顶部显示渐变色横幅：
```
🎯 自动驾驶 相关论文推荐
基于AI智能评估，精选与自动驾驶领域高度相关的最新研究论文
```

## 常见问题

### Q: 如何修改 SMTP 配置？
A: 编辑 `src/mailer/sender.py` 中的 `sendEmail()` 函数，修改 SMTP 服务器地址和端口。

### Q: 如何添加更多 ArXiv 分类？
A: 编辑 `src/arxiv/fetcher.py` 中的 `RSS_FEEDS` 字典。

### Q: 如何调整 AI 延迟时间？
A: 编辑 `src/ai/processor.py` 中 `process_papers_with_ai()` 函数的 `time.sleep(5)` 参数。

### Q: 如何自定义邮件颜色方案？
A: 编辑 `src/mailer/sender.py` 中的 `COLOR_SCHEMES` 列表。

### Q: 如何修改 AI Prompt？
A: 编辑 `src/ai/processor.py` 中 `process_abstract_with_ai()` 函数的 `prompt` 变量。

### Q: 模块命名为何用 `mailer` 而非 `email`？
A: 避免与 Python 标准库的 `email` 模块产生命名冲突。

## 开发指南

### 添加新功能模块

1. 在 `src/` 下创建新目录（如 `src/analyzer/`）
2. 创建 `__init__.py` 导出公共接口
3. 创建功能模块文件（如 `classifier.py`）
4. 在 `src/main.py` 中导入并使用

### 测试模块

```bash
# 测试单个模块
cd D:\workdir\Auto-Arxiv-Subscription
python -c "
import sys
sys.path.insert(0, 'src')
from arxiv import get_arxiv_data, filter_keywords
from ai import init_ai_client
from mailer import sendEmail, generate_email_html
print('模块导入成功！')
"
```

### 调试技巧

- 在 `src/main.py` 中添加 `pdb.set_trace()` 设置断点
- 查看各模块的 print 输出了解执行流程
- 检查 `papers/*.yaml` 文件验证去重功能
