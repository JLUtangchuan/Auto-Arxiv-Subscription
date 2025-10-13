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

def get_arxiv_data():
    """获取arxiv数据，包含标题、链接和摘要
    """
    dic = {}
    for k, v in rss_json.items():
        url = 'https://' + v
        r = requests.get(url)
        soup = bs(r.text, 'xml')
        items = soup.find_all('item')
        for i in range(len(items)):
            title = items[i].find('title').text.split("(arXiv")[0].strip()
            link = items[i].find('link').text
            
            # 获取摘要信息
            description = items[i].find('description').text
            # 清理摘要文本，去除HTML标签
            abstract_soup = bs(description, 'html.parser')
            abstract = abstract_soup.get_text().strip()
            
            # 存储为元组：(链接, 摘要)
            dic[title] = (link, abstract)
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
    # 获取arvix最新的文章
    dic = get_arxiv_data()
    # 读取keywords进行过滤
    res = filter_keywords(dic, args.keywords)
    # 发送到Email / 生成微信公众号推送
    if len(res) == 0:
        print("没有新的文章")
    else:
        # 添加CSS样式和JavaScript
        style_and_script = """
        <style>
            body { 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                background-color: #f8f9fa;
                padding: 20px;
            }
            h1 { 
                color: #333; 
                text-align: center;
                margin-bottom: 30px;
            }
            .keyword-section {
                margin-bottom: 30px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .keyword-header {
                padding: 15px 20px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s ease;
            }
            .keyword-header:hover {
                opacity: 0.9;
            }
            .keyword-title {
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
            .paper-count {
                background-color: rgba(255,255,255,0.3);
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 14px;
            }
            .toggle-icon {
                color: white;
                font-size: 20px;
                transition: transform 0.3s ease;
            }
            .toggle-icon.expanded {
                transform: rotate(180deg);
            }
            .keyword-content {
                display: none;
                padding: 20px;
            }
            .keyword-content.show {
                display: block;
            }
            .paper-item { 
                margin-bottom: 15px; 
                padding: 15px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .paper-title { 
                font-weight: bold; 
                margin-bottom: 10px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: start;
            }
            .paper-title-text {
                flex: 1;
                padding-right: 10px;
            }
            .abstract-toggle {
                font-size: 12px;
                padding: 3px 8px;
                border-radius: 3px;
                cursor: pointer;
                white-space: nowrap;
            }
            .paper-abstract { 
                margin-top: 10px;
                color: #666;
                text-align: justify;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                display: none;
                font-size: 14px;
                line-height: 1.8;
            }
            .paper-abstract.show {
                display: block;
            }
            .paper-link { 
                margin-top: 10px;
            }
            a { 
                text-decoration: none; 
                font-weight: 500;
            }
            a:hover { 
                text-decoration: underline; 
            }
        </style>
        <script>
            function toggleKeyword(keywordId) {
                const content = document.getElementById('content-' + keywordId);
                const icon = document.getElementById('icon-' + keywordId);
                content.classList.toggle('show');
                icon.classList.toggle('expanded');
            }
            
            function toggleAbstract(paperId) {
                const abstract = document.getElementById('abstract-' + paperId);
                const button = document.getElementById('btn-' + paperId);
                abstract.classList.toggle('show');
                button.textContent = abstract.classList.contains('show') ? '折叠摘要' : '展开摘要';
            }
            
            function expandAll() {
                document.querySelectorAll('.keyword-content').forEach(content => {
                    content.classList.add('show');
                });
                document.querySelectorAll('.toggle-icon').forEach(icon => {
                    icon.classList.add('expanded');
                });
            }
            
            function collapseAll() {
                document.querySelectorAll('.keyword-content').forEach(content => {
                    content.classList.remove('show');
                });
                document.querySelectorAll('.toggle-icon').forEach(icon => {
                    icon.classList.remove('expanded');
                });
            }
        </script>
        """
        
        main_html = []
        
        # 添加全局控制按钮
        control_buttons = """
        <div style="text-align: center; margin-bottom: 20px;">
            <button onclick="expandAll()" style="margin-right: 10px; padding: 8px 16px; border: none; background-color: #4CAF50; color: white; border-radius: 4px; cursor: pointer;">展开全部</button>
            <button onclick="collapseAll()" style="padding: 8px 16px; border: none; background-color: #f44336; color: white; border-radius: 4px; cursor: pointer;">折叠全部</button>
        </div>
        """
        
        for idx, (k, v) in enumerate(res.items()):
            # 为每个关键词分配颜色
            color_scheme = COLOR_SCHEMES[idx % len(COLOR_SCHEMES)]
            
            paper_html = []
            for paper_idx, (paper, link, abstract) in enumerate(v):
                # 限制摘要长度
                # if len(abstract) > 800:
                #     abstract = abstract[:800] + "..."
                
                paper_id = f"{idx}_{paper_idx}"
                paper_item = """
                <div class="paper-item">
                    <div class="paper-title">
                        <div class="paper-title-text" style="color: {color_dark};">{paper}</div>
                        <button id="btn-{paper_id}" class="abstract-toggle" onclick="toggleAbstract('{paper_id}')" 
                                style="background-color: {color_primary}; color: white; border: none;">
                            展开摘要
                        </button>
                    </div>
                    <div id="abstract-{paper_id}" class="paper-abstract">{abstract}</div>
                    <div class="paper-link">
                        <a href="{link}" target="_blank" style="color: {color_primary};">Read Paper →</a>
                    </div>
                </div>
                """.format(
                    paper=paper, 
                    abstract=abstract, 
                    link=link, 
                    paper_id=paper_id,
                    color_primary=color_scheme['primary'],
                    color_dark=color_scheme['dark']
                )
                paper_html.append(paper_item)
            
            paper_html = " ".join(paper_html)
            
            keyword_section = """
            <div class="keyword-section">
                <div class="keyword-header" onclick="toggleKeyword({idx})" 
                     style="background-color: {color_primary};">
                    <div class="keyword-title">Keyword: {subject}</div>
                    <div style="display: flex; align-items: center;">
                        <span class="paper-count">{paper_count} papers</span>
                        <span id="icon-{idx}" class="toggle-icon" style="margin-left: 10px;">▼</span>
                    </div>
                </div>
                <div id="content-{idx}" class="keyword-content" style="background-color: {color_light};">
                    {paper_html}
                </div>
            </div>
            """.format(
                idx=idx,
                subject=k, 
                paper_html=paper_html,
                paper_count=len(v),
                color_primary=color_scheme['primary'],
                color_light=color_scheme['light']
            )
            main_html.append(keyword_section)
        
        main_html = " ".join(main_html)

        today = datetime.date.today().__str__()
        content = """
        <html>
        <head>
            <meta charset="utf-8">
            {style_and_script}
        </head>
        <body>
            <h1>🚀 ArXiv Daily - {today}</h1>
            {control_buttons}
            {main_html}
        </body>
        </html>
        """.format(
            style_and_script=style_and_script, 
            today=today, 
            control_buttons=control_buttons,
            main_html=main_html
        )
        
        print(content)
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
