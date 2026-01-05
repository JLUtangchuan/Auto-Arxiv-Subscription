"""ArXiv RSS feed fetching and filtering."""

import datetime
import requests
from bs4 import BeautifulSoup as bs
from collections import defaultdict

# ArXiv RSS feeds configuration
RSS_FEEDS = {
    "AI": "export.arxiv.org/rss/cs.AI",
    "CV": "export.arxiv.org/rss/cs.CV",
    "CG": "export.arxiv.org/rss/cs.CG",
    "CL": "export.arxiv.org/rss/cs.CL",
    "ML": "export.arxiv.org/rss/stat.ML"
}


def get_arxiv_data():
    """Fetch today's papers from ArXiv RSS feeds.

    Returns:
        dict: Dictionary mapping paper titles to (link, abstract) tuples
    """
    dic = {}
    today = datetime.date.today().strftime('%Y-%m-%d')

    for category, feed_path in RSS_FEEDS.items():
        url = 'https://' + feed_path
        try:
            r = requests.get(url)
            soup = bs(r.text, 'xml')
            items = soup.find_all('item')

            for i in range(len(items)):
                # Get publication date
                pub_date = items[i].find('pubDate').text

                title = items[i].find('title').text.split("(arXiv")[0].strip()
                link = items[i].find('link').text

                # Get abstract
                description = items[i].find('description').text
                abstract_soup = bs(description, 'html.parser')
                abstract = abstract_soup.get_text().strip()

                # Store as tuple: (link, abstract)
                dic[title] = (link, abstract)
        except Exception as e:
            print(f"Error fetching {category} feed: {e}")
            continue

    print(f"已获取今天({today})的论文共 {len(dic)} 篇")
    return dic


def filter_keywords(papers_dict, keywords):
    """Filter papers by keywords (case-insensitive substring match in titles).

    Args:
        papers_dict: Dictionary mapping paper titles to (link, abstract) tuples
        keywords: List of keywords to filter by

    Returns:
        defaultdict: Dictionary mapping keywords to lists of (title, link, abstract) tuples
    """
    print("Keyword", keywords)
    res = defaultdict(list)

    for title, (link, abstract) in papers_dict.items():
        for keyword in keywords:
            if keyword.lower() in title.lower():
                res[keyword].append((title, link, abstract))

    return res
