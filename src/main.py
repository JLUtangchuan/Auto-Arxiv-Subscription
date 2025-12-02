#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   main.py
@Time    :   2022/04/29 18:09:53
@Author  :   Tang Chuan 
@Contact :   tangchuan20@mails.jlu.edu.cn
@Desc    :   自动发送邮件
'''

import argparse
import datetime
import json
import os
import poplib
import smtplib
import time
from email import parser
from email.header import Header
from email.mime.text import MIMEText
from collections import defaultdict

import requests
from bs4 import BeautifulSoup as bs
from openai import OpenAI
import pdb

rss_json = {
    "AI": "export.arxiv.org/rss/cs.AI",
    "CV": "export.arxiv.org/rss/cs.CV",
    "CG": "export.arxiv.org/rss/cs.CG",
    "CL": "export.arxiv.org/rss/cs.CL",
    "ML": "export.arxiv.org/rss/stat.ML"
}

# 预定义的颜色方案
COLOR_SCHEMES = [
    {'primary': '#FF6B6B', 'light': '#FFE5E5', 'dark': '#C92A2A'},
    {'primary': '#4ECDC4', 'light': '#D3F9F6', 'dark': '#087F8C'},
    {'primary': '#45B7D1', 'light': '#DAEDFF', 'dark': '#0C7FB0'},
    {'primary': '#96CEB4', 'light': '#E8F5EE', 'dark': '#5A9F7B'},
    {'primary': '#FECA57', 'light': '#FFF3D6', 'dark': '#F59E0B'},
    {'primary': '#A29BFE', 'light': '#E8E6FF', 'dark': '#6C5CE7'},
    {'primary': '#FD79A8', 'light': '#FFE0EC', 'dark': '#E84393'},
    {'primary': '#778BEB', 'light': '#E3E7FF', 'dark': '#546DE5'},
]

# 初始化OpenAI客户端
def init_ai_client():
    """初始化AI客户端"""
    try:
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            # base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        return client
    except Exception as e:
        print(f"AI客户端初始化失败: {e}")
        return None

def process_abstract_with_ai(client, title, abstract):
    """使用AI处理摘要，翻译并提取关键信息"""
    if not client:
        return abstract, "", []
    
    try:
        prompt = f"""
请对以下论文进行分析：

标题：{title}
摘要（英文）：{abstract}

请完成以下任务：
1. 将摘要翻译成中文
2. 提取3-5个核心技术关键词
3. 用一句话总结论文的主要贡献

请按以下JSON格式返回：
{{
    "chinese_abstract": "中文摘要翻译",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "main_contribution": "主要贡献总结"
}}
"""
        
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "qwen3-max-preview"),
            messages=[
                {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长翻译和提取关键信息。"},
                {"role": "user", "content": prompt},
            ],
        )
        
        # 解析AI返回的结果
        ai_response = completion.choices[0].message.content
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                chinese_abstract = result.get('chinese_abstract', abstract)
                keywords = result.get('keywords', [])
                main_contribution = result.get('main_contribution', '')
                return chinese_abstract, main_contribution, keywords
        except:
            pass
        
        # 如果JSON解析失败，返回原始响应
        return ai_response, "", []
        
    except Exception as e:
        print(f"AI处理失败: {e}")
        return abstract, "", []

def get_arxiv_data():
    """获取arxiv数据，包含标题、链接和摘要，只返回今天的论文
    """
    dic = {}
    # 获取今天的日期，格式为YYYY-MM-DD
    today = datetime.date.today()

    for k, v in rss_json.items():
        url = 'https://' + v
        r = requests.get(url)
        soup = bs(r.text, 'xml')
        items = soup.find_all('item')
        for i in range(len(items)):
            # 获取发布日期
            pub_date = items[i].find('pubDate').text
            
            # 解析日期
            try:
                # 将pubDate转换为datetime对象
                # RSS日期格式通常是类似 'Wed, 29 May 2024 00:00:00 GMT'
                pub_date_obj = datetime.datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                # 转换为date对象进行比较
                pub_date_date = pub_date_obj.date()
                
                # 计算日期差
                days_diff = (today - pub_date_date).days
                
                # 只保留2天内的论文（包括今天）
                if days_diff < 0 or days_diff > 2:
                    continue
            except ValueError:
                # 如果日期解析失败，跳过该论文
                continue
            
            title = items[i].find('title').text.split("(arXiv")[0].strip()
            link = items[i].find('link').text
            
            # 获取摘要信息
            description = items[i].find('description').text
            # 清理摘要文本，去除HTML标签
            abstract_soup = bs(description, 'html.parser')
            abstract = abstract_soup.get_text().strip()
            
            # 存储为元组：(链接, 原始摘要)
            dic[title] = (link, abstract)
    
    print(f"已获取今天({today})的论文共 {len(dic)} 篇")
    return dic


def filter_keywords(dic, keywords):
    """过滤关键词
    """
    print("Keyword", keywords)
    res = defaultdict(list)
    for k, v in dic.items():
        for w in keywords:
            if w.lower() in k.lower():
                # v现在是(link, abstract)元组
                res[w].append((k, v[0], v[1]))  # (title, link, abstract)
    return res

def process_papers_with_ai(filtered_papers, ai_client):
    """使用AI处理筛选后的论文"""
    processed_papers = defaultdict(list)
    
    for keyword, papers in filtered_papers.items():
        for title, link, abstract in papers:
            print(f"正在处理论文: {title[:50]}...")
            
            # 使用AI处理摘要
            chinese_abstract, main_contribution, ai_keywords = process_abstract_with_ai(
                ai_client, title, abstract
            )
            
            # 存储处理后的信息
            processed_papers[keyword].append({
                'title': title,
                'link': link,
                'original_abstract': abstract,
                'chinese_abstract': chinese_abstract,
                'main_contribution': main_contribution,
                'ai_keywords': ai_keywords
            })
            
            # API调用间隔5秒
            time.sleep(5)
    
    return processed_papers

def sendEmail(msg_from, msg_to, auth_id, title, content):
    """发送邮件目前只支持qq邮箱自动发送邮件
    """
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg['Subject'] = title
    msg['From'] = msg_from
    msg['To'] = msg_to
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com",465)
        s.login(msg_from, auth_id)
        s.sendmail(msg_from, msg_to, msg.as_string())
        print("发送成功")
    except s.SMTPException:
        print("发送失败")
    finally:
        s.quit()


def main(args):
    # 初始化AI客户端
    ai_client = init_ai_client()
    if not ai_client:
        print("警告：AI客户端初始化失败，将使用原始摘要")
    
    # 获取arvix最新的文章
    dic = get_arxiv_data()
    # 读取keywords进行过滤
    filtered_res = filter_keywords(dic, args.keywords)
    
    # 使用AI处理论文
    if ai_client and len(filtered_res) > 0:
        print("开始使用AI处理论文...")
        res = process_papers_with_ai(filtered_res, ai_client)
    else:
        # 如果AI不可用，转换为旧格式
        res = {}
        for k, v in filtered_res.items():
            res[k] = []
            for title, link, abstract in v:
                res[k].append({
                    'title': title,
                    'link': link,
                    'original_abstract': abstract,
                    'chinese_abstract': abstract,
                    'main_contribution': '',
                    'ai_keywords': []
                })
    
    # 发送到Email
    if len(res) == 0:
        print("没有新的文章")
    else:
        # 添加CSS样式（包含新的AI处理内容样式）
        style = """
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6; 
                background-color: #f8f9fa;
                padding: 20px;
                color: #333;
            }
            h1 { 
                color: #333; 
                text-align: center;
                margin-bottom: 30px;
            }
            /* Details 和 Summary 样式 */
            details {
                margin-bottom: 20px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                background-color: white;
            }
            details[open] summary {
                border-bottom: 2px solid rgba(255,255,255,0.3);
            }
            summary {
                padding: 15px 20px;
                cursor: pointer;
                list-style: none;
                outline: none;
                font-weight: bold;
                font-size: 18px;
                color: white;
                transition: all 0.3s ease;
            }
            summary:hover {
                opacity: 0.9;
            }
            summary::-webkit-details-marker {
                display: none;
            }
            summary::before {
                content: "▶ ";
                display: inline-block;
                margin-right: 10px;
                transition: transform 0.3s ease;
            }
            details[open] summary::before {
                transform: rotate(90deg);
            }
            .keyword-badge {
                float: right;
                background-color: rgba(255,255,255,0.3);
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 14px;
                font-weight: normal;
            }
            .keyword-content {
                padding: 20px;
            }
            /* 论文项样式 */
            .paper-details {
                margin-bottom: 15px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden;
                background-color: white;
            }
            .paper-summary {
                padding: 12px 15px;
                cursor: pointer;
                list-style: none;
                background-color: #f8f9fa;
                font-weight: 600;
                color: #333;
                font-size: 15px;
                line-height: 1.5;
            }
            .paper-summary:hover {
                background-color: #f0f0f0;
            }
            .paper-summary::-webkit-details-marker {
                display: none;
            }
            .paper-content {
                padding: 15px;
                background-color: white;
            }
            .main-contribution {
                background-color: #e8f4fd;
                border-left: 4px solid #1890ff;
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
                font-weight: 500;
                color: #2c3e50;
            }
            .ai-keywords {
                margin: 10px 0;
            }
            .ai-keyword-tag {
                display: inline-block;
                background-color: #52c41a;
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                margin: 2px 4px 2px 0;
                font-weight: 500;
            }
            .paper-abstract { 
                margin: 10px 0;
                color: #666;
                text-align: justify;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                font-size: 14px;
                line-height: 1.8;
                border-left: 3px solid #ddd;
            }
            .chinese-abstract {
                background-color: #f0f8f0;
                border-left: 3px solid #52c41a;
            }
            .original-abstract {
                background-color: #f8f8f8;
                border-left: 3px solid #999;
            }
            .paper-link { 
                margin-top: 10px;
                text-align: right;
            }
            a { 
                text-decoration: none; 
                font-weight: 500;
                padding: 5px 15px;
                border-radius: 4px;
                display: inline-block;
                color: white;
            }
            a:hover { 
                opacity: 0.8;
            }
            .abstract-label {
                font-weight: bold;
                color: #555;
                margin-bottom: 5px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .ai-badge {
                background-color: #722ed1;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                margin-left: 8px;
            }
        </style>
        """
        
        main_html = []
        
        for idx, (k, papers) in enumerate(res.items()):
            # 为每个关键词分配颜色
            color_scheme = COLOR_SCHEMES[idx % len(COLOR_SCHEMES)]
            
            paper_html = []
            for paper in papers:
                # 构建AI关键词标签
                ai_keywords_html = ""
                if paper['ai_keywords']:
                    keyword_tags = [f'<span class="ai-keyword-tag">{kw}</span>' for kw in paper['ai_keywords']]
                    ai_keywords_html = f'<div class="ai-keywords"><strong>🏷️ AI提取关键词：</strong>{" ".join(keyword_tags)}</div>'
                
                # 构建主要贡献部分
                contribution_html = ""
                if paper['main_contribution']:
                    contribution_html = f'<div class="main-contribution">💡 <strong>主要贡献：</strong>{paper["main_contribution"]}</div>'
                
                paper_item = """
                <details class="paper-details">
                    <summary class="paper-summary">
                        {title}
                        {ai_badge}
                    </summary>
                    <div class="paper-content">
                        {contribution_html}
                        {ai_keywords_html}
                        <div class="abstract-label">中文摘要 (AI翻译)</div>
                        <div class="paper-abstract chinese-abstract">{chinese_abstract}</div>
                        <details>
                            <summary style="font-size: 12px; color: #666; padding: 5px 0; border: none; background: none;">
                                📄 查看原文摘要
                            </summary>
                            <div class="paper-abstract original-abstract">{original_abstract}</div>
                        </details>
                        <div class="paper-link">
                            <a href="{link}" target="_blank" style="background-color: {color_primary};">
                                Read Full Paper →
                            </a>
                        </div>
                    </div>
                </details>
                """.format(
                    title=paper['title'],
                    chinese_abstract=paper['chinese_abstract'],
                    original_abstract=paper['original_abstract'],
                    link=paper['link'],
                    color_primary=color_scheme['primary'],
                    contribution_html=contribution_html,
                    ai_keywords_html=ai_keywords_html,
                    ai_badge='<span class="ai-badge">AI增强</span>' if ai_client else ''
                )
                paper_html.append(paper_item)
            
            paper_html = "\n".join(paper_html)
            
            keyword_section = """
            <details>
                <summary style="background-color: {color_primary};">
                    Keyword: {subject}
                    <span class="keyword-badge">{paper_count} papers</span>
                </summary>
                <div class="keyword-content" style="background-color: {color_light};">
                    {paper_html}
                </div>
            </details>
            """.format(
                subject=k, 
                paper_html=paper_html,
                paper_count=len(papers),
                color_primary=color_scheme['primary'],
                color_light=color_scheme['light']
            )
            main_html.append(keyword_section)
        
        main_html = "\n".join(main_html)

        today = datetime.date.today().__str__()
        content = """
        <html>
        <head>
            <meta charset="utf-8">
            {style}
        </head>
        <body>
            <h1>🚀 ArXiv Daily - {today} {ai_status}</h1>
            <div style="text-align: center; margin-bottom: 20px; color: #666; font-size: 14px;">
                Click on keywords to expand papers, click on paper titles to view abstracts
                {ai_description}
            </div>
            {main_html}
        </body>
        </html>
        """.format(
            style=style, 
            today=today, 
            main_html=main_html,
            ai_status="🤖" if ai_client else "",
            ai_description="<br><span style='color: #722ed1;'>✨ 本期内容由AI增强：中文翻译 + 关键信息提取</span>" if ai_client else ""
        )
        
        print("生成邮件内容成功")
        sendEmail(args.email, args.receiver, args.token, args.title, content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The Description')
    parser.add_argument('-e','--email', type=str, default=None, required=True, help='发送邮件的邮箱')
    parser.add_argument('-t','--token', type=str, default=None, required=True, help='发送邮件的邮箱的授权码')
    parser.add_argument('-r','--receiver', type=str, default=None, required=True, help='接收邮件的邮箱')
    parser.add_argument('-k','--keywords', nargs='+', default=None)
    args = parser.parse_args()
    args.title = "arxiv Daily"
    
    main(args)