import json
from datetime import datetime
from typing import Dict, List

class HTMLGenerator:
    """生成复古终端风格的HTML页面"""

    def __init__(self, data_file='data.json'):
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def generate_news_item(self, item: Dict, category: str) -> str:
        """生成单个新闻项的HTML"""
        category_map = {
            'funding': ('💰 FUNDING', 'tag-funding'),
            'product': ('🔧 PRODUCT', 'tag-product'),
            'paper': ('📄 PAPER', 'tag-paper'),
            'news': ('📰 新闻', 'tag-news')
        }

        tag_text, tag_class = category_map.get(category, ('📰 NEWS', 'tag-news'))

        title = item.get('title', 'Untitled')
        description = item.get('description', item.get('summary', ''))
        link = item.get('link', '#')
        source = item.get('source', 'Unknown')

        # 计算时间差
        timestamp = item.get('timestamp', item.get('published', ''))
        time_ago = self.format_time_ago(timestamp)

        return f'''
                <div class="news-item show" data-category="{category}">
                    <span class="news-tag {tag_class}">[{tag_text}]</span>
                    <div class="news-title">{title}</div>
                    <div class="news-meta">
                        {description}
                        <br>
                        <a href="{link}" class="news-link">> Read more</a> | {time_ago} | Source: {source}
                    </div>
                </div>
'''

    def format_time_ago(self, timestamp_str: str) -> str:
        """格式化时间为"X hours ago"格式"""
        try:
            if not timestamp_str:
                return "recently"

            # 解析时间戳
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

            # 当前时间（使用本地时区）
            from datetime import timezone

            # 如果timestamp没有时区信息，加上本地时区
            if timestamp.tzinfo is None:
                # 假设是UTC时间（因为arXiv等都用UTC）
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)

            # 转为UTC比较
            if timestamp.tzinfo:
                timestamp = timestamp.astimezone(timezone.utc)

            delta = now - timestamp

            hours = int(delta.total_seconds() / 3600)
            if hours < 1:
                minutes = int(delta.total_seconds() / 60) if delta.total_seconds() > 0 else 0
                if minutes <= 1:
                    return "just now"
                return f"{minutes} min ago"
            elif hours == 1:
                return "1 hour ago"
            elif hours < 24:
                return f"{hours} hours ago"
            elif hours < 48:
                return "1 day ago"
            else:
                days = int(hours / 24)
                return f"{days} days ago"
        except Exception as e:
            print(f"Error formatting time: {e}")
            return "recently"

    def calculate_robot_mood(self, total_items: int) -> Dict:
        """根据信息数量计算机器人心情"""
        if total_items >= 30:
            return {
                'status': 'OVERLOADED! 🚀',
                'quote': '"嘀嘀嘀！信息太多了！我的小脑袋快装不下啦！但是好开心~"',
                'percentage': 95,
                'css_class': 'mood-excited'
            }
        elif total_items >= 16:
            return {
                'status': 'EXCITED!',
                'quote': f'"哇哇哇！今天有{total_items}条新信息！我要把这些都存到记忆库里~"',
                'percentage': 80,
                'css_class': 'mood-excited'
            }
        elif total_items >= 6:
            return {
                'status': 'HAPPY',
                'quote': '"嘿嘿，今天学到了一些有趣的东西！我最喜欢学习新知识了~"',
                'percentage': 60,
                'css_class': 'mood-happy'
            }
        else:
            return {
                'status': 'SLEEPY...',
                'quote': '"呼噜噜...今天好安静呀...机器人们是不是都去睡觉了？我也想睡..."',
                'percentage': 30,
                'css_class': 'mood-sleepy'
            }

    def generate_html(self, output_file='index.html'):
        """生成完整的HTML页面"""
        # 收集所有数据
        all_items = []
        counts = {
            'funding': len(self.data['data'].get('funding', [])),
            'product': len(self.data['data'].get('products', [])),
            'paper': len(self.data['data'].get('papers', [])),
            'news': len(self.data['data'].get('news', []))
        }

        total_items = sum(counts.values())

        # 生成新闻项HTML
        news_html = ""
        for category, items in self.data['data'].items():
            # 统一转成单数形式匹配tab的data-category
            cat_name = {
                'papers': 'paper',
                'products': 'product',
                'news': 'news',
                'funding': 'funding'
            }.get(category, category)
            for item in items:
                news_html += self.generate_news_item(item, cat_name)

        # 计算机器人心情
        mood = self.calculate_robot_mood(total_items)

        # 格式化更新时间
        last_updated = datetime.fromisoformat(self.data['last_updated'])
        formatted_time = last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')

        # 生成摘要统计和关键洞察
        stats_text = f"🤖 {counts['paper']} papers | 💰 {counts['funding']} funding | 🔧 {counts['product']} product | 📰 {counts['news']} news | 🔥 {total_items} total"

        # 提取关键公司提及
        mentioned_companies = []
        # 从数据中查找公司名称
        companies = self.data.get('companies_tracked', KEY_COMPANIES if 'KEY_COMPANIES' in locals() else [])
        for company in companies[:5]:  # 检查前5个
            company_lower = str(company).lower()
            company_count = 0
            for cat in ['papers', 'news', 'funding', 'products']:
                for item in self.data['data'].get(cat, []):
                    if company_lower in str(item.get('title', '')).lower() or \
                       company_lower in str(item.get('summary', '')).lower():
                        company_count += 1
            if company_count > 0:
                mentioned_companies.append(f"{company} ({company_count})")

        # 生成关键洞察
        key_insight = ""
        if counts['funding'] > 0:
            key_insight = f"💰 Funding activity detected - {counts['funding']} investment deal(s)"
        elif counts['paper'] > 0:
            key_insight = f"📄 Strong research momentum - {counts['paper']} new papers on robotics & embodied AI"
        elif counts['product'] > 0:
            key_insight = f"🔧 Product updates - {counts['product']} new developments in humanoid robotics"
        else:
            key_insight = "📰 Following industry news and research trends..."

        # 读取模板并替换
        # 这里我们直接嵌入完整的HTML
        html_content = self.get_html_template(
            total_items=total_items,
            counts=counts,
            mood=mood,
            stats_text=stats_text,
            key_insight=key_insight,
            mentioned_companies=mentioned_companies,
            companies_tracked=self.data.get('companies_tracked', []),
            news_html=news_html,
            last_updated=formatted_time
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Generated {output_file}")
        print(f"   Total items: {total_items}")

    def get_html_template(self, **kwargs) -> str:
        """返回HTML模板"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EMBODIED AI TRACKER</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: #0a0a0a;
            color: #ffb000;
            font-family: 'IBM Plex Mono', 'Courier New', monospace;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }}

        /* CRT扫描线效果 */
        body::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.15),
                rgba(0, 0, 0, 0.15) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 1000;
            animation: scanline 8s linear infinite;
        }}

        @keyframes scanline {{
            0% {{ transform: translateY(0); }}
            100% {{ transform: translateY(10px); }}
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}

        /* 头部 */
        .header {{
            border: 2px solid #ffb000;
            padding: 15px;
            margin-bottom: 20px;
            background: rgba(255, 176, 0, 0.05);
        }}

        .header h1 {{
            font-size: 24px;
            text-align: center;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }}

        .status-bar {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            padding: 5px 0;
            border-top: 1px solid #ffb000;
            margin-top: 10px;
        }}

        /* 机器人学习状态 */
        .robot-status {{
            border: 2px solid #00ff00;
            padding: 15px;
            margin-bottom: 20px;
            background: rgba(0, 255, 0, 0.03);
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .robot-avatar {{
            font-size: 16px;
            line-height: 1.1;
            white-space: pre;
            color: #00ff00;
            animation: robotBounce 2s ease-in-out infinite;
            font-family: monospace;
        }}

        @keyframes robotBounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-5px); }}
        }}

        .robot-info {{
            flex: 1;
        }}

        .robot-mood {{
            font-size: 18px;
            color: #00ff00;
            margin-bottom: 5px;
            font-weight: bold;
        }}

        .robot-stats {{
            font-size: 12px;
            color: #ffb000;
            margin-top: 5px;
        }}

        .knowledge-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
        }}

        .knowledge-meter {{
            flex: 1;
            height: 20px;
            border: 1px solid #00ff00;
            position: relative;
            background: rgba(0, 255, 0, 0.1);
        }}

        .knowledge-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00ff00, #00ff00 50%, #ffb000 100%);
            transition: width 1s ease-out;
            animation: shimmer 3s linear infinite;
        }}

        @keyframes shimmer {{
            0% {{ background-position: -100% 0; }}
            100% {{ background-position: 100% 0; }}
        }}

        /* 摘要区块 */
        .digest {{
            border: 2px solid #00ff00;
            padding: 15px;
            margin-bottom: 20px;
            background: rgba(0, 255, 0, 0.03);
        }}

        .digest-title {{
            color: #00ff00;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .digest-title::before {{
            content: ">>";
            animation: blink 1s step-start infinite;
        }}

        @keyframes blink {{
            50% {{ opacity: 0; }}
        }}

        .digest-stats {{
            color: #00ff00;
            margin-bottom: 10px;
            font-size: 14px;
        }}

        .digest-content {{
            color: #ffb000;
            line-height: 1.6;
            font-size: 14px;
        }}

        .digest-key-insight {{
            color: #ffcc00;
            margin-bottom: 12px;
            padding: 10px;
            background: rgba(255, 176, 0, 0.1);
            border-left: 3px solid #ffcc00;
            margin-top: 8px;
            font-size: 13px;
            font-weight: bold;
        }}

        .digest-companies {{
            color: #00cccc;
            margin-bottom: 8px;
            font-size: 13px;
        }}

        /* 新闻列表 */
        .news-section {{
            border: 2px solid #ffb000;
            padding: 0;
            margin-bottom: 20px;
        }}

        /* Tab切换 */
        .news-tabs {{
            display: flex;
            background: rgba(255, 176, 0, 0.1);
            border-bottom: 2px solid #ffb000;
        }}

        .tab-item {{
            flex: 1;
            padding: 12px 20px;
            text-align: center;
            cursor: pointer;
            color: #ffb000;
            border-right: 1px solid #ffb000;
            transition: all 0.3s;
            font-size: 13px;
            font-weight: bold;
        }}

        .tab-item:last-child {{
            border-right: none;
        }}

        .tab-item:hover {{
            background: rgba(255, 176, 0, 0.2);
        }}

        .tab-item.active {{
            background: #ffb000;
            color: #0a0a0a;
        }}

        .news-content {{
            padding: 15px;
        }}

        .section-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px dashed #ffb000;
        }}

        .news-item {{
            margin-bottom: 15px;
            padding: 10px;
            border-left: 3px solid #00ff00;
            padding-left: 15px;
            transition: all 0.3s;
            cursor: pointer;
            display: none;
        }}

        .news-item.show {{
            display: block;
        }}

        .news-item:hover {{
            background: rgba(255, 176, 0, 0.1);
            transform: translateX(5px);
            border-left-width: 5px;
        }}

        .news-tag {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
            margin-right: 10px;
            border: 1px solid;
        }}

        .tag-funding {{
            color: #00ff00;
            border-color: #00ff00;
        }}

        .tag-product {{
            color: #00d4ff;
            border-color: #00d4ff;
        }}

        .tag-paper {{
            color: #ff00ff;
            border-color: #ff00ff;
        }}

        .tag-news {{
            color: #ffb000;
            border-color: #ffb000;
        }}

        .news-title {{
            font-size: 14px;
            margin: 5px 0;
            color: #ffffff;
        }}

        .news-meta {{
            font-size: 11px;
            color: #888;
            margin-top: 5px;
        }}

        .news-link {{
            color: #00ff00;
            text-decoration: none;
            border-bottom: 1px dotted #00ff00;
        }}

        .news-link:hover {{
            color: #00ff00;
            text-decoration: none;
            animation: flicker 0.5s;
        }}

        @keyframes flicker {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}

        /* 底部导航 */
        .nav {{
            display: flex;
            gap: 20px;
            justify-content: center;
            padding: 15px;
            border: 2px solid #ffb000;
            background: rgba(255, 176, 0, 0.05);
            flex-wrap: wrap;
        }}

        .nav-item {{
            color: #ffb000;
            text-decoration: none;
            padding: 5px 15px;
            border: 1px solid #ffb000;
            transition: all 0.3s;
            position: relative;
        }}

        .nav-item:hover {{
            background: #ffb000;
            color: #0a0a0a;
            transform: scale(1.05);
            box-shadow: 0 0 10px #ffb000;
        }}

        .nav-item:active {{
            transform: scale(0.95);
        }}

        /* 响应式 */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header h1 {{
                font-size: 18px;
            }}

            .robot-status {{
                flex-direction: column;
                text-align: center;
            }}

            .robot-avatar {{
                font-size: 14px;
            }}

            .news-tabs {{
                flex-wrap: wrap;
            }}

            .tab-item {{
                flex: 1 1 50%;
                border-bottom: 1px solid #ffb000;
            }}
        }}

        /* 机器人不同心情的样式 */
        .mood-excited .robot-avatar {{
            color: #00ff00;
            animation: robotExcited 0.5s ease-in-out infinite;
        }}

        @keyframes robotExcited {{
            0%, 100% {{ transform: translateY(0) rotate(-1deg); }}
            50% {{ transform: translateY(-8px) rotate(1deg); }}
        }}

        .mood-happy .robot-avatar {{
            color: #00ff00;
        }}

        .mood-normal .robot-avatar {{
            color: #ffb000;
        }}

        .mood-sleepy .robot-avatar {{
            color: #888;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>╔═══════════════════════════════════════════════╗</h1>
            <h1>║  EMBODIED INTELLIGENCE TRACKER               ║</h1>
            <h1>╚═══════════════════════════════════════════════╝</h1>
            <div class="status-bar">
                <div>STATUS: SYSTEM READY ✓</div>
                <div>LAST SCAN: {kwargs['last_updated']}</div>
            </div>
        </div>

        <!-- 机器人学习状态 -->
        <div class="robot-status {kwargs['mood']['css_class']}">
            <div class="robot-avatar"> ___
(◕‿◕)
 ---
 _|_
|   |
 oo</div>
            <div class="robot-info">
                <div class="robot-mood">🤖 WALL-E STATUS: {kwargs['mood']['status']}</div>
                <div style="color: #ffb000; font-size: 13px; margin-bottom: 8px;">
                    {kwargs['mood']['quote']}
                </div>
                <div class="robot-stats">
                    📚 Today's Learning: {kwargs['total_items']} items | 💰 {kwargs['counts']['funding']} funding deals | 📄 {kwargs['counts']['paper']} papers | 🔧 {kwargs['counts']['product']} product updates
                </div>
                <div class="knowledge-bar">
                    <span style="color: #00ff00; font-size: 11px;">KNOWLEDGE:</span>
                    <div class="knowledge-meter">
                        <div class="knowledge-fill" style="width: {kwargs['mood']['percentage']}%;"></div>
                    </div>
                    <span style="color: #00ff00; font-size: 11px;">{kwargs['mood']['percentage']}%</span>
                </div>
            </div>
        </div>

        <!-- 今日摘要 -->
        <div class="digest">
            <div class="digest-title">TODAY'S DIGEST</div>
            <div class="digest-stats">
                {kwargs['stats_text']}
            </div>
            <div class="digest-key-insight">
                {kwargs['key_insight']}
            </div>
'''
        # 添加公司提及
        if kwargs.get('mentioned_companies'):
            html_content += f'''
            <div class="digest-companies">
                🏢 COMPANIES: {', '.join(kwargs['mentioned_companies'][:3])}
            </div>
'''
        html_content += f'''
            <div class="digest-content">
                📄 LAST UPDATE: {kwargs['last_updated']} | 🌐 TRACKING: {len(kwargs.get('mentioned_companies', [])) + len(kwargs.get('companies_tracked', [kwargs.get('total_items', 0)]))} key companies
            </div>
        </div>

        <!-- 新闻列表（带Tab切换） -->
        <div class="news-section">
            <!-- Tab导航 -->
            <div class="news-tabs">
                <div class="tab-item active" data-category="all">
                    [ALL] ({kwargs['total_items']})
                </div>
                <div class="tab-item" data-category="funding">
                    [💰 FUNDING] ({kwargs['counts']['funding']})
                </div>
                <div class="tab-item" data-category="product">
                    [🔧 PRODUCT] ({kwargs['counts']['product']})
                </div>
                <div class="tab-item" data-category="paper">
                    [📄 PAPER] ({kwargs['counts']['paper']})
                </div>
                <div class="tab-item" data-category="news">
                    [📰 新闻] ({kwargs['counts']['news']})
                </div>
            </div>

            <!-- 新闻内容 -->
            <div class="news-content">
                <div class="section-title">┌─ LAST 24 HOURS ─────────────────────────────────┐</div>

{kwargs['news_html']}

                <div class="section-title">└──────────────────────────────────────────────────┘</div>
            </div>
        </div>

        <!-- 底部导航 -->
        <div class="nav">
            <a href="#home" class="nav-item" title="返回首页">[HOME]</a>
            <a href="#timeline" class="nav-item" title="按月时间线">[TIMELINE]</a>
            <a href="#search" class="nav-item" title="搜索">[SEARCH]</a>
        </div>

        <!-- 页脚信息 -->
        <div style="text-align: center; margin-top: 30px; padding: 20px; border-top: 1px dashed #ffb000; color: #888; font-size: 11px;">
            <p>TRACKING THE FUTURE WITH RETRO STYLE | POWERED BY EMBODIED AI TRACKER</p>
            <p style="margin-top: 5px;">🤖 MAKING ROBOTS SMARTER, ONE DAY AT A TIME</p>
        </div>
    </div>

    <script>
        // Tab切换功能
        document.querySelectorAll('.tab-item').forEach(tab => {{
            tab.addEventListener('click', function() {{
                // 更新active状态
                document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // 筛选新闻
                const category = this.dataset.category;
                const newsItems = document.querySelectorAll('.news-item');

                newsItems.forEach(item => {{
                    if (category === 'all' || item.dataset.category === category) {{
                        item.classList.add('show');
                    }} else {{
                        item.classList.remove('show');
                    }}
                }});
            }});
        }});

        // 新闻项点击效果
        document.querySelectorAll('.news-item').forEach(item => {{
            item.addEventListener('click', function() {{
                this.style.transition = 'all 0.2s';
                const originalBg = this.style.background;
                this.style.background = 'rgba(0,255,0,0.2)';
                setTimeout(() => {{
                    this.style.background = originalBg;
                }}, 300);
            }});
        }});

        // 随机闪烁效果
        setInterval(() => {{
            const items = document.querySelectorAll('.news-item.show');
            if (items.length > 0) {{
                const randomItem = items[Math.floor(Math.random() * items.length)];
                randomItem.style.opacity = '0.7';
                setTimeout(() => {{
                    randomItem.style.opacity = '1';
                }}, 100);
            }}
        }}, 5000);
    </script>
</body>
</html>'''

if __name__ == '__main__':
    generator = HTMLGenerator()
    generator.generate_html()
