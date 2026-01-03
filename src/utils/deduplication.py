"""Paper deduplication utilities using YAML storage."""

import datetime
import os
import yaml


def load_previous_papers():
    """Load previous day's paper records for deduplication.

    Returns:
        set: Set of paper titles from the previous day
    """
    papers_dir = "papers"
    previous_papers = set()

    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    yaml_path = os.path.join(papers_dir, f"{yesterday_str}.yaml")

    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'papers' in data:
                    previous_papers = set(data['papers'])
                    print(f"加载前一天的论文记录: {len(previous_papers)} 篇")
        except Exception as e:
            print(f"加载前一天论文记录失败: {e}")

    return previous_papers


def save_today_papers(papers_dict):
    """Save today's paper titles to YAML file.

    Args:
        papers_dict: Dictionary mapping paper titles to (link, abstract) tuples
    """
    papers_dir = "papers"

    # Create papers directory if it doesn't exist
    if not os.path.exists(papers_dir):
        os.makedirs(papers_dir)
        print(f"创建目录: {papers_dir}")

    # Get today's date
    today = datetime.date.today().strftime('%Y-%m-%d')
    yaml_path = os.path.join(papers_dir, f"{today}.yaml")

    # Extract all paper titles
    paper_titles = list(papers_dict.keys())

    # Build YAML data structure
    data = {
        'date': today,
        'total_count': len(paper_titles),
        'papers': paper_titles
    }

    # Save to YAML file
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"保存今天的论文记录到: {yaml_path}")
    except Exception as e:
        print(f"保存论文记录失败: {e}")
