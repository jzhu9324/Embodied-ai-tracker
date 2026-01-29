import requests
import feedparser
from datetime import datetime, timedelta
import json
from typing import List, Dict
import time

class EmbodiedAIScraper:
    """具身智能信息爬虫"""

    def __init__(self):
        self.keywords = [
            'humanoid robot', 'embodied ai', 'embodied intelligence',
            'figure ai', 'tesla optimus', 'physical intelligence',
            'dexterous manipulation', 'robotic hand', 'biped robot',
            '人形机器人', '具身智能', '灵巧手'
        ]
        self.results = {
            'papers': [],
            'news': [],
            'funding': [],
            'products': []
        }

    def scrape_arxiv(self):
        """抓取arXiv论文"""
        print("📄 Scraping arXiv papers...")

        query = ' OR '.join([f'"{kw}"' for kw in self.keywords[:6]])
        base_url = 'http://export.arxiv.org/api/query?'

        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': 20,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:12]:
                paper = {
                    'title': entry.title,
                    'authors': ', '.join([author.name for author in entry.authors[:3]]),
                    'summary': entry.summary[:200] + '...',
                    'link': entry.link,
                    'published': entry.published,
                    'category': 'paper',
                    'source': 'arXiv'
                }
                self.results['papers'].append(paper)

            print(f"  ✓ Found {len(self.results['papers'])} papers")
        except Exception as e:
            print(f"  ✗ Error scraping arXiv: {e}")

    def scrape_hackernews(self):
        """抓取Hacker News讨论"""
        print("💬 Scraping Hacker News...")

        try:
            # 获取最新故事
            url = 'https://hacker-news.firebaseio.com/v0/newstories.json'
            response = requests.get(url, timeout=10)
            story_ids = response.json()[:100]

            count = 0
            for story_id in story_ids:
                if count >= 5:
                    break

                story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                story_response = requests.get(story_url, timeout=10)
                story = story_response.json()

                if story and 'title' in story:
                    title_lower = story['title'].lower()
                    if any(kw.lower() in title_lower for kw in ['robot', 'ai', 'tesla', 'optimus', 'figure']):
                        news_item = {
                            'title': story['title'],
                            'link': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'source': 'Hacker News',
                            'category': 'news',
                            'timestamp': datetime.fromtimestamp(story['time']).isoformat()
                        }
                        self.results['news'].append(news_item)
                        count += 1

                time.sleep(0.1)

            print(f"  ✓ Found {count} relevant stories")
        except Exception as e:
            print(f"  ✗ Error scraping Hacker News: {e}")

    def scrape_reddit(self):
        """抓取Reddit讨论"""
        print("🤖 Scraping Reddit...")

        subreddits = ['robotics', 'MachineLearning']

        try:
            for subreddit in subreddits:
                url = f'https://www.reddit.com/r/{subreddit}/new.json'
                headers = {'User-Agent': 'EmbodiedAI-Tracker/1.0'}

                response = requests.get(url, headers=headers, timeout=10)
                data = response.json()

                for post in data['data']['children'][:10]:
                    post_data = post['data']
                    title_lower = post_data['title'].lower()

                    if any(kw.lower() in title_lower for kw in self.keywords[:8]):
                        news_item = {
                            'title': post_data['title'],
                            'link': f"https://www.reddit.com{post_data['permalink']}",
                            'source': f'r/{subreddit}',
                            'category': 'news',
                            'timestamp': datetime.fromtimestamp(post_data['created_utc']).isoformat()
                        }
                        self.results['news'].append(news_item)

                time.sleep(1)

            print(f"  ✓ Found {len([n for n in self.results['news'] if 'reddit' in n['link']])} Reddit posts")
        except Exception as e:
            print(f"  ✗ Error scraping Reddit: {e}")

    def add_mock_data(self):
        """添加模拟数据（用于演示和测试）"""
        print("🎭 Adding mock data for demonstration...")

        # 融资信息
        self.results['funding'].extend([
            {
                'title': 'Physical Intelligence closes massive $600M Series B',
                'description': 'Led by Capital G (Alphabet), valuation reaches $5.6B',
                'link': '#',
                'category': 'funding',
                'source': 'TechCrunch',
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': '中国银河通用机器人完成3亿美元融资',
                'description': '宁德时代、中国移动、美团战投联合领投',
                'link': '#',
                'category': 'funding',
                'source': '36氪',
                'timestamp': (datetime.now() - timedelta(hours=12)).isoformat()
            }
        ])

        # 产品信息
        self.results['products'].extend([
            {
                'title': 'Figure AI demos Gen 3 dexterous hands in factory setting',
                'description': '12-DoF hands show unprecedented manipulation capability',
                'link': '#',
                'category': 'product',
                'source': 'Figure AI Blog',
                'timestamp': (datetime.now() - timedelta(hours=5)).isoformat()
            },
            {
                'title': 'Tesla Optimus Gen 3 spotted in Fremont factory floor',
                'description': 'Significant improvements in locomotion and load-bearing',
                'link': '#',
                'category': 'product',
                'source': 'Twitter/X',
                'timestamp': (datetime.now() - timedelta(hours=15)).isoformat()
            },
            {
                'title': '宇树科技G1人形机器人价格降至9.9万元',
                'description': '量产规模扩大带来成本下降',
                'link': '#',
                'category': 'product',
                'source': '宇树科技官网',
                'timestamp': (datetime.now() - timedelta(hours=20)).isoformat()
            }
        ])

    def save_results(self, filename='data.json'):
        """保存抓取结果"""
        output = {
            'last_updated': datetime.now().isoformat(),
            'total_items': sum(len(v) for v in self.results.values()),
            'data': self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Saved {output['total_items']} items to {filename}")

    def run(self):
        """执行所有爬虫"""
        print("🤖 Starting Embodied AI Tracker scraper...\n")

        self.scrape_arxiv()
        time.sleep(1)

        self.scrape_hackernews()
        time.sleep(1)

        self.scrape_reddit()
        time.sleep(1)

        self.add_mock_data()

        self.save_results()

        print("\n🎉 Scraping completed!")
        print(f"   Papers: {len(self.results['papers'])}")
        print(f"   News: {len(self.results['news'])}")
        print(f"   Funding: {len(self.results['funding'])}")
        print(f"   Products: {len(self.results['products'])}")

if __name__ == '__main__':
    scraper = EmbodiedAIScraper()
    scraper.run()
