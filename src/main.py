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
    """获取arxiv数据
    """
    dic = {}
    for k, v in rss_json.items():
        url = 'https://' + v
        r = requests.get(url)
        soup = bs(r.text, 'xml')
        items = soup.find_all('item')
        for i in range(len(items)):
            # print(items[i].find('title').text.split("(arXiv")[0].strip(), items[i].find('link').text)
            dic[items[i].find('title').text.split("(arXiv")[0].strip()] = items[i].find('link').text
    return dic


def filter_keywords(dic, keywords):
    """过滤关键词
    """
    res = [(k, v) for k, v in dic.items() if any(map(lambda y: y.lower() in k.lower(), keywords))]
    return list(res)

def sendEmail(msg_from, msg_to, auth_id, title, content):
    """发送邮件目前只支持qq邮箱自动发送邮件
    """
    msg = MIMEText(content)
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
        content = "\n".join(["{} {}".format(k, v) for k, v in res])
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
    