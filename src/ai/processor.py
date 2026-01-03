"""AI processing for paper abstracts using DashScope API."""

import json
import os
import time
import re
from collections import defaultdict
from openai import OpenAI


def init_ai_client():
    """Initialize the AI client for DashScope API.

    Returns:
        OpenAI client instance or None if initialization fails
    """
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        return client
    except Exception as e:
        print(f"AI客户端初始化失败: {e}")
        return None


def process_abstract_with_ai(client, title, abstract, domain):
    """Process paper abstract with AI for translation and analysis.

    Args:
        client: OpenAI client instance
        title: Paper title
        abstract: Paper abstract (English)
        domain: Target domain for relevance scoring

    Returns:
        tuple: (chinese_abstract, main_contribution, keywords, relevance_score)
    """
    if not client:
        return abstract, "", [], 0

    try:
        prompt = f"""
请对以下论文进行分析：

标题：{title}
摘要（英文）：{abstract}
目标领域：{domain}

请完成以下任务：
1. 将摘要翻译成中文
2. 提取3-5个核心技术关键词
3. 用一句话总结论文的主要贡献
4. 评估该论文与"{domain}"领域的关联程度（1-5分，5分表示最相关，1分表示基本不相关）

请按以下JSON格式返回：
{{
    "chinese_abstract": "中文摘要翻译",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "main_contribution": "主要贡献总结",
    "relevance_score": 关联程度评分(1-5的整数)
}}
"""

        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "qwen3-max-preview"),
            messages=[
                {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长翻译和提取关键信息。"},
                {"role": "user", "content": prompt},
            ],
        )

        # Parse AI response
        ai_response = completion.choices[0].message.content

        # Try to parse JSON
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                chinese_abstract = result.get('chinese_abstract', abstract)
                keywords = result.get('keywords', [])
                main_contribution = result.get('main_contribution', '')
                relevance_score = result.get('relevance_score', 3)
                # Ensure score is in 1-5 range
                relevance_score = max(1, min(5, int(relevance_score)))
                return chinese_abstract, main_contribution, keywords, relevance_score
        except:
            pass

        # If JSON parsing fails, return raw response
        return ai_response, "", [], 3

    except Exception as e:
        print(f"AI处理失败: {e}")
        return abstract, "", [], 3


def process_papers_with_ai(filtered_papers, ai_client, domain):
    """Process filtered papers with AI for translation and analysis.

    Args:
        filtered_papers: Dictionary mapping keywords to lists of (title, link, abstract) tuples
        ai_client: OpenAI client instance
        domain: Target domain for relevance scoring

    Returns:
        defaultdict: Dictionary mapping keywords to lists of processed paper dictionaries
    """
    processed_papers = defaultdict(list)

    for keyword, papers in filtered_papers.items():
        for title, link, abstract in papers:
            print(f"正在处理论文: {title[:50]}...")

            # Process abstract with AI
            chinese_abstract, main_contribution, ai_keywords, relevance_score = process_abstract_with_ai(
                ai_client, title, abstract, domain
            )

            # Store processed information
            processed_papers[keyword].append({
                'title': title,
                'link': link,
                'original_abstract': abstract,
                'chinese_abstract': chinese_abstract,
                'main_contribution': main_contribution,
                'ai_keywords': ai_keywords,
                'relevance_score': relevance_score
            })

            # 5-second delay between API calls
            time.sleep(5)

    return processed_papers
