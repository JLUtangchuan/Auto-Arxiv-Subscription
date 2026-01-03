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
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arxiv import get_arxiv_data, filter_keywords
from ai import init_ai_client, process_papers_with_ai
from mailer import sendEmail, generate_email_html
from utils import load_previous_papers, save_today_papers


def main(args):
    """Main application workflow.

    Args:
        args: Parsed command line arguments
    """
    # Initialize AI client
    ai_client = init_ai_client()
    if not ai_client:
        print("警告：AI客户端初始化失败，将使用原始摘要")

    # Fetch latest ArXiv papers
    dic = get_arxiv_data()

    # Save today's paper records
    save_today_papers(dic)

    # Load previous day's paper records
    previous_papers = load_previous_papers()

    # Remove papers from previous day
    if previous_papers:
        original_count = len(dic)
        dic = {k: v for k, v in dic.items() if k not in previous_papers}
        removed_count = original_count - len(dic)
        if removed_count > 0:
            print(f"跳过前一天已发送的论文: {removed_count} 篇")

    # Filter by keywords
    filtered_res = filter_keywords(dic, args.keywords)

    # Process papers with AI
    if ai_client and len(filtered_res) > 0:
        print("开始使用AI处理论文...")
        res = process_papers_with_ai(filtered_res, ai_client, args.domain)
    else:
        # If AI is unavailable, convert to old format
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
                    'ai_keywords': [],
                    'relevance_score': 3  # Default score
                })

    # Send email
    if len(res) == 0:
        print("没有新的文章")
    else:
        # Generate email HTML content
        content = generate_email_html(res, ai_client, args.domain)
        print("生成邮件内容成功")
        sendEmail(args.email, args.receiver, args.token, args.title, content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ArXiv Daily Paper Notification System')
    parser.add_argument('-e', '--email', type=str, required=True,
                       help='发送邮件的邮箱')
    parser.add_argument('-t', '--token', type=str, required=True,
                       help='发送邮件的邮箱的授权码')
    parser.add_argument('-r', '--receiver', type=str, required=True,
                       help='接收邮件的邮箱')
    parser.add_argument('-k', '--keywords', nargs='+', default=None,
                       help='搜索关键词列表')
    parser.add_argument('-d', '--domain', type=str, default='自动驾驶',
                       help='目标领域名称，用于相关性评分')
    args = parser.parse_args()
    args.title = "arxiv Daily"

    main(args)
