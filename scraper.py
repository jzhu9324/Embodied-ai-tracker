import requests
import feedparser
from datetime import datetime, timedelta
import json
from typing import List, Dict
import time
import re

class EmbodiedAIScraper:
    """具身智能信息爬虫"""

    def __init__(self):
        # 扩充关键词，更宽松的匹配
        self.keywords = [
            # 英文关键词
            'robot', 'humanoid', 'embodied ai', 'embodied intelligence',
            'figure ai', 'tesla optimus', 'optimus', 'physical intelligence',
            'dexterous', 'manipulation', 'robotic hand', 'biped',
            'unitree', 'boston dynamics', 'agility robotics', '1x',
            # 中文关键词
            '人形机器人', '具身智能', '灵巧手', '双足', '机器人',
            '优必选', '宇树', '银河通用', '傅利叶', '智元',
            '小米机器人', '阿里巴巴机器人', '腾讯机器人'
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

        # 放宽查询条件 - 分别搜索然后合并
        queries = [
            'cat:cs.RO AND (robot OR humanoid OR manipulation)',
            'cat:cs.AI AND (embodied)',
            'cat:cs.CV AND (robot)'
        ]

        total_papers = 0
        seen_papers = set()

        try:
            for query in queries:
                base_url = 'http://export.arxiv.org/api/query?'

                params = {
                    'search_query': query,
                    'start': 0,
                    'max_results': 10,
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }

                response = requests.get(base_url, params=params, timeout=10)
                feed = feedparser.parse(response.content)

                for entry in feed.entries:
                    # 用ID去重
                    paper_id = entry.id.split('/abs/')[-1].split('v')[0]
                    if paper_id in seen_papers:
                        continue
                    seen_papers.add(paper_id)

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
                    total_papers += 1

                    if total_papers >= 15:
                        break

                time.sleep(1)
                if total_papers >= 15:
                    break

            print(f"  ✓ Found {total_papers} papers")
        except Exception as e:
            print(f"  ✗ Error scraping arXiv: {e}")

    def scrape_hackernews(self):
        """抓取Hacker News讨论"""
        print("💬 Scraping Hacker News...")

        try:
            # 获取最新故事 - 扩大搜索范围
            url = 'https://hacker-news.firebaseio.com/v0/newstories.json'
            response = requests.get(url, timeout=10)
            story_ids = response.json()[:200]  # 检查更多条目

            count = 0
            for story_id in story_ids:
                if count >= 10:
                    break

                story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                story_response = requests.get(story_url, timeout=10)
                story = story_response.json()

                if story and 'title' in story:
                    title_lower = story['title'].lower()
                    # 更宽松的匹配
                    if any(kw.lower() in title_lower for kw in ['robot', 'ai', 'tesla', 'optimus', 'human', 'machine']):
                        # 判断类别
                        category = 'news'
                        if any(kw in title_lower for kw in ['fund', 'raise', 'investment', 'funding', 'million', 'billion']):
                            category = 'funding'
                        elif any(kw in title_lower for kw in ['product', 'launch', 'release', 'demo', 'unveiled']):
                            category = 'product'

                        news_item = {
                            'title': story['title'],
                            'link': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'source': 'Hacker News',
                            'category': category,
                            'timestamp': datetime.fromtimestamp(story['time']).isoformat()
                        }
                        self.results[category + 's' if category != 'news' else 'news'].append(news_item)
                        count += 1

                time.sleep(0.05)  # 减少延迟

            print(f"  ✓ Found {count} relevant stories")
        except Exception as e:
            print(f"  ✗ Error scraping Hacker News: {e}")

    def scrape_zhihu(self):
        """尝试爬取知乎热门（简单版）"""
        print("📝 Trying to scrape Chinese sources...")
        # 知识星球和36氪需要更复杂的爬虫，暂时跳过
        print("  ℹ️ Chinese sources need more complex scraping - skipping for now")

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
        print("🎭 Mock data disabled - showing only real scraped data...")
        pass  # 不添加任何模拟数据

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

        self.scrape_zhihu()
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
        print(f"   Total: {sum(len(v) for v in self.results.values())} items")

if __name__ == '__main__':
    scraper = EmbodiedAIScraper()
    scraper.run()
