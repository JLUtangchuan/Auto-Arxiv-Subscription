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
        # 添加CSS样式
        style = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            h1 { color: #333; }
            h2 { color: #555; margin-top: 30px; }
            .paper-item { 
                margin-bottom: 20px; 
                padding: 15px;
                background-color: #f5f5f5;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .paper-title { 
                font-weight: bold; 
                color: #333;
                margin-bottom: 10px;
            }
            .paper-abstract { 
                margin-top: 10px;
                color: #666;
                text-align: justify;
                padding: 10px;
                background-color: #fff;
                border-radius: 3px;
            }
            .paper-link { 
                margin-top: 10px;
            }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
        """
        
        main_html = []
        for k, v in res.items():
            paper_html = []
            for paper, link, abstract in v:
                # 限制摘要长度，如果太长可以截断
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                
                paper_item = """
                <div class="paper-item">
                    <div class="paper-title">{paper}</div>
                    <div class="paper-abstract">{abstract}</div>
                    <div class="paper-link"><a href="{link}" target="_blank">Read Paper →</a></div>
                </div>
                """.format(paper=paper, abstract=abstract, link=link)
                paper_html.append(paper_item)
            
            paper_html = " ".join(paper_html)
            res_html = """
            <h2>Keyword: {subject}</h2>
            {paper_html}
            """.format(subject=k, paper_html=paper_html)
            main_html.append(res_html)
        
        main_html = " ".join(main_html)

        today = datetime.date.today().__str__()
        content = """
        <html>
        <head>
            {style}
        </head>
        <body>
            <h1>ArXiv Daily - {today}</h1>
            {main_html}
        </body>
        </html>
        """.format(style=style, today=today, main_html=main_html)
        
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
