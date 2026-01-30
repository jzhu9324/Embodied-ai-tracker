#!/usr/bin/env python3
import requests
import feedparser
from datetime import datetime, timedelta
import json
from typing import List, Dict
import time
import re

# ==================== 配置 ====================
# 关键公司白名单
KEY_COMPANIES = [
    # 英文
    'tesla', 'optimus', 'figure ai', '1x', 'e-ve',
    'unitree', 'agility robotics', 'boston dynamics', 'anybotics',
    'physical intelligence', 'pi', 'sanctuary ai',
    'fourier intelligence', 'agility robotics',
    # 中文
    '优必选', 'ubtech', '银河通用', '傅利叶', '智元', '宇树', '达闼'
]

# 常用关键词（用于非公司相关内容）
GENERAL_KEYWORDS = [
    'humanoid', 'embodied', 'manipulation', 'grasping',
    'robot learning', 'sim2real', 'dexterous'
]

# 配置参数
MAX_PAPERS = 10  # arXiv最多10篇
MAX_HN = 5       # Hacker News最多5条
MAX_NEWS = 5     # 其他新闻最多5条
DAYS_CUTOFF = 7  # 论文只取最近7天
MIN_HN_POINTS = 50  # HN最少50分

class EmbodiedAIScraper:
    """具身智能信息爬虫 - 方案A：精简版"""

    def __init__(self):
        self.results = {
            'papers': [],
            'news': [],
            'funding': [],
            'products': []
        }

    def is_company_related(self, text: str) -> bool:
        """检查是否与公司相关（高优先级）"""
        text_lower = text.lower()
        return any(company.lower() in text_lower for company in KEY_COMPANIES)

    def is_relevant(self, text: str) -> bool:
        """检查是否相关（公司或关键内容）"""
        return self.is_company_related(text) or any(kw.lower() in text.lower() for kw in GENERAL_KEYWORDS)

    def scrape_arxiv(self):
        """抓取arXiv论文 - 只取最近7天高质量论文"""
        print("📄 Scraping arXiv papers (last 7 days)...")

        # 合并查询 - 机器人相关
        query = 'cat:cs.RO AND (' + ' OR '.join(GENERAL_KEYWORDS[:4]) + ')'

        try:
            base_url = 'http://export.arxiv.org/api/query?'
            params = {
                'search_query': query,
                'start': 0,
                'max_results': 50,  # 先多抓一些，再筛选
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }

            response = requests.get(base_url, params=params, timeout=10)
            feed = feedparser.parse(response.content)

            cutoff_date = datetime.now() - timedelta(days=DAYS_CUTOFF)
            seen_papers = set()
            company_papers = []  # 公司相关论文（高优先级）
            other_papers = []     # 其他论文

            for entry in feed.entries:
                paper_id = entry.id.split('/abs/')[-1].split('v')[0]
                if paper_id in seen_papers:
                    continue
                seen_papers.add(paper_id)

                # 解析发布时间
                try:
                    published = datetime.fromisoformat(entry.published.replace('Z', '+00:00'))
                    published = published.replace(tzinfo=None) if published.tzinfo else published
                except:
                    continue

                paper = {
                    'title': entry.title,
                    'authors': ', '.join([author.name for author in entry.authors[:3]]),
                    'summary': entry.summary[:150] + '...',
                    'link': entry.link,
                    'published': entry.published,
                    'category': 'paper',
                    'source': 'arXiv'
                }

                # 分类：公司相关优先
                if self.is_company_related(entry.title):
                    company_papers.append(paper)
                elif self.is_relevant(entry.title):
                    other_papers.append(paper)

            # 公司相关论文优先，最多5篇
            for paper in company_papers[:5]:
                self.results['papers'].append(paper)

            # 其他论文，补充到10篇
            remaining = MAX_PAPERS - len(self.results['papers'])
            for paper in other_papers[:remaining]:
                self.results['papers'].append(paper)

            print(f"  ✓ Found {len(self.results['papers'])} papers (company: {len(company_papers)}, other: {len(other_papers)})")

        except Exception as e:
            print(f"  ✗ Error scraping arXiv: {e}")

    def scrape_hackernews(self):
        """抓取Hacker News - 只取高赞讨论"""
        print("💬 Scraping Hacker News (points > {MIN_HN_POINTS})...")

        try:
            url = 'https://hacker-news.firebaseio.com/v0/newstories.json'
            response = requests.get(url, timeout=10)
            story_ids = response.json()[:200]

            company_items = []  # 公司相关
            high_quality = []  # 高赞但非公司

            for story_id in story_ids:
                if len(company_items) + len(high_quality) >= MAX_HN * 2:
                    break

                story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                story_response = requests.get(story_url, timeout=5)
                story = story_response.json()

                if not story or 'title' not in story:
                    continue

                score = story.get('score', 0)
                title_lower = story['title'].lower()

                # 必须高赞 OR 公司相关
                if score >= MIN_HN_POINTS and self.is_relevant(title_lower):
                    item = {
                        'title': story['title'],
                        'link': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        'source': f'Hacker News ({score} pts)',
                        'category': 'news',
                        'timestamp': datetime.fromtimestamp(story['time']).isoformat()
                    }

                    # 自动分类
                    if any(kw in title_lower for kw in ['fund', 'raise', 'investment', 'funding', 'million', 'billion', 'series']):
                        item['category'] = 'funding'
                    elif any(kw in title_lower for kw in ['launch', 'release', 'demo', 'unveil', 'announce']):
                        item['category'] = 'product'

                    if self.is_company_related(title_lower):
                        company_items.append(item)
                    else:
                        high_quality.append(item)

                time.sleep(0.02)

            # 公司相关优先
            for item in company_items[:3]:
                self.results[item['category'] + 's' if item['category'] != 'news' else 'news'].append(item)

            # 补充高赞
            remaining = MAX_HN - len(company_items)
            for item in high_quality[:remaining]:
                self.results[item['category'] + 's' if item['category'] != 'news' else 'news'].append(item)

            print(f"  ✓ Found {len(company_items) + len(high_quality)} HN stories")

        except Exception as e:
            print(f"  ✗ Error scraping Hacker News: {e}")

    def scrape_techcrunch_ai(self):
        """抓取TechCrunch AI RSS - 只取公司相关"""
        print("📰 Scraping TechCrunch AI RSS (company-related)...")

        rss_url = 'https://techcrunch.com/category/artificial-intelligence/feed/'

        try:
            feed = feedparser.parse(rss_url)

            count = 0
            for entry in feed.entries[:30]:  # 检查最近30条
                if count >= MAX_NEWS:
                    break

                title = entry.get('title', '')
                title_lower = title.lower()

                # 只取公司相关 OR 重要新闻
                summary = entry.get('summary', '')
                if self.is_company_related(title_lower + summary.lower()) or \
                   any(kw in title_lower for kw in ['tesla optimus', 'figure ai', '1x robot', 'humanoid robot', 'boston dynamics']):

                    category = 'news'
                    if any(kw in title_lower for kw in ['fund', 'raise', 'investment', 'series', 'million', 'billion', 'acquired']):
                        category = 'funding'

                    self.results[category + 's' if category != 'news' else 'news'].append({
                        'title': title,
                        'link': entry.get('link', ''),
                        'source': 'TechCrunch',
                        'category': category,
                        'timestamp': entry.get('published', datetime.now().isoformat())
                    })
                    count += 1

            print(f"  ✓ Found {count} TechCrunch articles")

        except Exception as e:
            print(f"  ✗ Error scraping TechCrunch: {e}")

    def run(self):
        """执行所有爬虫"""
        print(f"🤖 Embodied AI Tracker - High Quality Mode")
        print(f"📋 Target: ~20-30 high-quality items")
        print(f"🏢 Tracking: {len(KEY_COMPANIES)} companies")
        print()

        timestamp = datetime.now()
        cutoff_date = timestamp - timedelta(days=DAYS_CUTOFF)
        print(f"📅 Paper cutoff: Last {DAYS_CUTOFF} days (since {cutoff_date.strftime('%Y-%m-%d')})")
        print(f"🎯 HN points threshold: {MIN_HN_POINTS}")
        print()

        self.scrape_arxiv()
        time.sleep(0.5)

        self.scrape_hackernews()
        time.sleep(0.5)

        self.scrape_techcrunch_ai()
        time.sleep(0.5)

        self.save_results()

        total = sum(len(v) for v in self.results.values())

        print("\n" + "="*50)
        print("🎉 SCRAPING COMPLETED")
        print("="*50)
        print(f"📄 Papers:   {len(self.results['papers'])}")
        print(f"💰 Funding:  {len(self.results['funding'])}")
        print(f"🔧 Products: {len(self.results['products'])}")
        print(f"📰 News:     {len(self.results['news'])}")
        print(f"-" * 50)
        print(f"📊 TOTAL:    {total} items")
        print("="*50)

    def save_results(self, filename='data.json'):
        """保存抓取结果"""
        output = {
            'last_updated': datetime.now().isoformat(),
            'total_items': sum(len(v) for v in self.results.values()),
            'companies_tracked': KEY_COMPANIES,
            'data': self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Saved {output['total_items']} items to {filename}")

if __name__ == '__main__':
    scraper = EmbodiedAIScraper()
    scraper.run()
