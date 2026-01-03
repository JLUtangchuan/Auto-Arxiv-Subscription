"""Email generation and sending functionality."""

import datetime
import smtplib
from email.mime.text import MIMEText

# Predefined color schemes for email sections
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


def generate_email_html(processed_papers, ai_client, domain):
    """Generate HTML email content from processed papers.

    Args:
        processed_papers: Dictionary mapping keywords to lists of processed paper dictionaries
        ai_client: AI client instance (for AI badge display)
        domain: Target domain name

    Returns:
        str: Complete HTML email content
    """
    # CSS styles
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
        /* Details and Summary styles */
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
        /* Paper item styles */
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
        .relevance-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .relevance-5 {
            background-color: #52c41a;
            color: white;
        }
        .relevance-4 {
            background-color: #1890ff;
            color: white;
        }
        .relevance-3 {
            background-color: #faad14;
            color: white;
        }
        .relevance-2 {
            background-color: #ff4d4f;
            color: white;
        }
        .relevance-1 {
            background-color: #8c8c8c;
            color: white;
        }
        .relevance-stars {
            color: #faad14;
            font-size: 14px;
            margin-left: 5px;
        }
        .domain-header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .domain-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .domain-description {
            font-size: 14px;
            opacity: 0.9;
        }
    </style>
    """

    main_html = []

    for idx, (keyword, papers) in enumerate(processed_papers.items()):
        # Assign color scheme for each keyword
        color_scheme = COLOR_SCHEMES[idx % len(COLOR_SCHEMES)]

        paper_html = []
        for paper in papers:
            # Build AI keyword tags
            ai_keywords_html = ""
            if paper['ai_keywords']:
                keyword_tags = [f'<span class="ai-keyword-tag">{kw}</span>' for kw in paper['ai_keywords']]
                ai_keywords_html = f'<div class="ai-keywords"><strong>🏷️ AI提取关键词：</strong>{" ".join(keyword_tags)}</div>'

            # Build main contribution section
            contribution_html = ""
            if paper['main_contribution']:
                contribution_html = f'<div class="main-contribution">💡 <strong>主要贡献：</strong>{paper["main_contribution"]}</div>'

            # Build relevance score
            relevance_score = paper.get('relevance_score', 3)
            stars = '★' * relevance_score + '☆' * (5 - relevance_score)
            relevance_text = {
                5: '非常相关',
                4: '相关',
                3: '一般',
                2: '不太相关',
                1: '不相关'
            }.get(relevance_score, '一般')

            paper_item = """
            <details class="paper-details">
                <summary class="paper-summary">
                    {title}
                    <span class="relevance-badge relevance-{score}">{relevance_text}</span>
                    <span class="relevance-stars">{stars}</span>
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
                ai_badge='<span class="ai-badge">AI增强</span>' if ai_client else '',
                score=relevance_score,
                relevance_text=relevance_text,
                stars=stars
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
            subject=keyword,
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
        {domain_header}
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
        domain_header=f"""
        <div class="domain-header">
            <div class="domain-title">🎯 {domain} 相关论文推荐</div>
            <div class="domain-description">基于AI智能评估，精选与{domain}领域高度相关的最新研究论文</div>
        </div>
        """ if ai_client else "",
        ai_description="<br><span style='color: #722ed1;'>✨ 本期内容由AI增强：中文翻译 + 关键信息提取 + 相关性评分</span>" if ai_client else ""
    )

    return content


def sendEmail(msg_from, msg_to, auth_id, title, content):
    """Send email via QQ Mail SMTP.

    Args:
        msg_from: Sender email address
        msg_to: Recipient email address
        auth_id: Email authorization code/password
        title: Email subject
        content: Email content (HTML format)
    """
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg['Subject'] = title
    msg['From'] = msg_from
    msg['To'] = msg_to

    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(msg_from, auth_id)
        s.sendmail(msg_from, msg_to, msg.as_string())
        print("发送成功")
    except s.SMTPException:
        print("发送失败")
    finally:
        s.quit()
