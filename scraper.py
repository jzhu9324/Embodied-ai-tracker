import requests
import feedparser
from datetime import datetime, timedelta
import json
from typing import List, Dict
import time
import re

class EmbodiedAIScraper:
    """具身智能信息爬虫 - 增强版"""

    def __init__(self):
        self.keywords = [
            # 英文关键词
            'robot', 'humanoid', 'embodied ai', 'embodied intelligence',
            'figure ai', 'tesla optimus', 'optimus', 'physical intelligence',
            'dexterous', 'manipulation', 'robotic hand', 'biped',
            'unitree', 'boston dynamics', 'agility robotics', '1x',
            'robot learning', 'reinforcement learning', 'sim2real',
            # 中文关键词
            '人形机器人', '具身智能', '灵巧手', '双足', '机器人',
            '优必选', '宇树', '银河通用', '傅利叶', '智元'
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

        queries = [
            'cat:cs.RO AND (robot OR humanoid OR manipulation OR grasping)',
            'cat:cs.AI AND (embodied OR robot learning OR sim2real)',
            'cat:cs.CV AND (robot OR manipulation OR visual servoing)',
            'cat:cs.LG AND (robot learning OR reinforcement)',
        ]

        total_papers = 0
        seen_papers = set()

        try:
            for query in queries:
                base_url = 'http://export.arxiv.org/api/query?'
                params = {
                    'search_query': query,
                    'start': 0,
                    'max_results': 15,
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }

                response = requests.get(base_url, params=params, timeout=10)
                feed = feedparser.parse(response.content)

                for entry in feed.entries:
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

                time.sleep(1)

            print(f"  ✓ Found {total_papers} papers")
        except Exception as e:
            print(f"  ✗ Error scraping arXiv: {e}")

    def scrape_huggingface(self):
        """抓取Hugging Face论文和模型"""
        print("🤗 Scraping Hugging Face...")

        try:
            # Hugging Face papers API
            papers_url = 'https://huggingface.co/api/papers'
            response = requests.get(papers_url, timeout=15)

            if response.status_code == 200:
                papers_data = response.json()
                count = 0

                for paper in papers_data[:20]:
                    title_lower = paper.get('title', '').lower()
                    # 匹配机器人/AI相关
                    if any(kw in title_lower for kw in ['robot', 'embodied', 'manipulation', 'action', 'navigation']):
                        self.results['papers'].append({
                            'title': paper.get('title', 'Untitled'),
                            'authors': ', '.join(paper.get('authors', [])[:3]),
                            'summary': paper.get('summary', '')[:200] + '...',
                            'link': f"https://huggingface.co/papers/{paper.get('paperId', '')}",
                            'published': paper.get('publishedAt', datetime.now().isoformat()),
                            'category': 'paper',
                            'source': 'Hugging Face'
                        })
                        count += 1

                print(f"  ✓ Found {count} HF papers")
        except Exception as e:
            print(f"  ✗ Error scraping Hugging Face: {e}")

        try:
            # Hugging Face trending models
            models_url = 'https://huggingface.co/api/models'
            params = {
                'limit': 50,
                'sort': 'downloads',
                'direction': '-1'
            }
            response = requests.get(models_url, params=params, timeout=15)

            if response.status_code == 200:
                models_data = response.json()
                count = 0

                for model in models_data:
                    name = model.get('modelId', '')
                    name_lower = name.lower()
                    desc = model.get('cardData', {}).get('description', '')
                    desc_lower = desc.lower()

                    # 匹配机器人相关模型
                    if any(kw in name_lower + desc_lower for kw in ['robot', 'embodied', 'manipulation', 'gripper']):
                        self.results['products'].append({
                            'title': f"HF Model: {name}",
                            'description': desc[:150] + '...',
                            'link': f"https://huggingface.co/{name}",
                            'source': 'Hugging Face',
                            'category': 'product',
                            'timestamp': datetime.now().isoformat()
                        })
                        count += 1

                    if count >= 10:
                        break

                print(f"  ✓ Found {count} HF models")
        except Exception as e:
            print(f"  ✗ Error scraping HF models: {e}")

    def scrape_tech_news(self):
        """抓取技术新闻RSS"""
        print("📰 Scraping Tech News RSS...")

        rss_feeds = [
            ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/'),
            ('The Verge AI', 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml'),
            ('MIT Tech Review', 'https://www.technologyreview.com/feed/'),
            ('Wired AI', 'https://www.wired.com/category/artificial-intelligence/feed/'),
        ]

        count = 0
        seen_urls = set()

        for feed_name, feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    if count >= 20:
                        break

                    url = entry.get('link', '')
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = entry.get('title', '')
                    title_lower = title.lower()
                    summary = entry.get('summary', '')[:200]

                    # 匹配机器人/AI
                    if any(kw in title_lower + summary.lower() for kw in ['robot', 'humanoid', 'tesla optimus', 'figure ai', 'unitree', 'boston dynamics']):
                        # 判断类别
                        category = 'news'
                        if any(kw in title_lower for kw in ['fund', 'raise', 'investment', 'funding', 'million', 'billion']):
                            category = 'funding'
                        elif any(kw in title_lower for kw in ['launch', 'release', 'demo', 'unveiled', 'new model']):
                            category = 'product'

                        self.results[category + 's' if category != 'news' else 'news'].append({
                            'title': title,
                            'link': url,
                            'source': feed_name,
                            'category': category,
                            'timestamp': entry.get('published', datetime.now().isoformat()),
                            'summary': summary
                        })
                        count += 1

                time.sleep(0.5)
            except Exception as e:
                print(f"  ✗ Error scraping {feed_name}: {e}")

        print(f"  ✓ Found {count} news from RSS")

    def scrape_hackernews(self):
        """抓取Hacker News讨论"""
        print("💬 Scraping Hacker News...")

        try:
            url = 'https://hacker-news.firebaseio.com/v0/newstories.json'
            response = requests.get(url, timeout=10)
            story_ids = response.json()[:300]

            count = 0
            for story_id in story_ids:
                if count >= 15:
                    break

                story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                story_response = requests.get(story_url, timeout=10)
                story = story_response.json()

                if story and 'title' in story:
                    title_lower = story['title'].lower()
                    if any(kw.lower() in title_lower for kw in ['robot', 'ai', 'tesla', 'optimus', 'figure', 'humanoid', 'unitree']):
                        category = 'news'
                        if any(kw in title_lower for kw in ['fund', 'raise', 'investment', 'funding', 'million', 'billion']):
                            category = 'funding'
                        elif any(kw in title_lower for kw in ['product', 'launch', 'release', 'demo']):
                            category = 'product'

                        self.results[category + 's' if category != 'news' else 'news'].append({
                            'title': story['title'],
                            'link': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'source': 'Hacker News',
                            'category': category,
                            'timestamp': datetime.fromtimestamp(story['time']).isoformat()
                        })
                        count += 1

                time.sleep(0.03)

            print(f"  ✓ Found {count} HN stories")
        except Exception as e:
            print(f"  ✗ Error scraping Hacker News: {e}")

    def scrape_reddit(self):
        """抓取Reddit讨论"""
        print("🤖 Scraping Reddit...")

        subreddits = ['robotics', 'MachineLearning', 'artificial', 'EmbodiedAI']

        try:
            for subreddit in subreddits:
                url = f'https://www.reddit.com/r/{subreddit}/new.json'
                headers = {'User-Agent': 'EmbodiedAI-Tracker/1.0'}

                response = requests.get(url, headers=headers, timeout=10)
                data = response.json()

                for post in data['data']['children'][:15]:
                    post_data = post['data']
                    title_lower = post_data['title'].lower()

                    # 更宽松的匹配
                    if any(kw.lower() in title_lower for kw in ['robot', 'humanoid', 'embodied', 'manipulation', 'gripper', 'vision', 'navigation']):
                        self.results['news'].append({
                            'title': post_data['title'],
                            'link': f"https://www.reddit.com{post_data['permalink']}",
                            'source': f'r/{subreddit}',
                            'category': 'news',
                            'timestamp': datetime.fromtimestamp(post_data['created_utc']).isoformat()
                        })

                time.sleep(0.5)

            print(f"  ✓ Found Reddit posts")
        except Exception as e:
            print(f"  ✗ Error scraping Reddit: {e}")

    def run(self):
        """执行所有爬虫"""
        print("🤖 Starting Enhanced Embodied AI Tracker scraper...\n")

        self.scrape_arxiv()
        time.sleep(0.5)

        self.scrape_huggingface()
        time.sleep(0.5)

        self.scrape_tech_news()
        time.sleep(0.5)

        self.scrape_hackernews()
        time.sleep(0.5)

        self.scrape_reddit()
        time.sleep(0.5)

        self.save_results()

        total = sum(len(v) for v in self.results.values())
        print("\n🎉 Scraping completed!")
        print(f"   Papers: {len(self.results['papers'])}")
        print(f"   News: {len(self.results['news'])}")
        print(f"   Funding: {len(self.results['funding'])}")
        print(f"   Products: {len(self.results['products'])}")
        print(f"   TOTAL: {total} items")

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

if __name__ == '__main__':
    scraper = EmbodiedAIScraper()
    scraper.run()
