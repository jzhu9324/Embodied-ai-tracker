# 具身智能追踪器增强设计

**日期**: 2026-02-03
**状态**: 待实施
**设计者**: Claude + User

## 1. 背景和目标

### 当前问题
1. 数据源单一（仅 arXiv、HN、TechCrunch）
2. 公司列表固定，无法动态发现新公司
3. Today's Digest 过于简单，缺乏深度分析

### 改进目标
- **扩展数据源**: 从 3 个增加到 11+ 个，覆盖中英文媒体、学术、社交平台
- **智能公司管理**: 三层列表 + 自动发现机制，快速跟踪新兴公司
- **AI 智能摘要**: 技术趋势分析、公司动态关联、行业影响评估
- **自动化流程**: 每天早上 7-9 点自动更新，一键查看

## 2. 整体架构

### 系统流程
```
数据抓取 (scraper.py)
   ↓ (多源并发抓取)
数据存储 (data.json)
   ↓
AI 分析 (Claude Code)
   ↓
生成摘要 (digests/YYYY-MM-DD-digest.md)
   ↓
生成 HTML (generator.py)
   ↓
部署 (GitHub Pages)
```

### 核心组件
1. **多源数据抓取器** - 插件化架构，每个源独立可配置
2. **公司管理系统** - 三层列表（核心/观察/待审核）
3. **AI 智能分析器** - Claude Code 本地分析，生成 Markdown 摘要
4. **前端展示器** - 渲染摘要和数据

## 3. 数据源扩展设计

### 新增数据源清单

#### 中文科技媒体（4个）
- **机器之心**: `https://www.jiqizhixin.com/rss`
- **量子位**: 网页抓取（无 RSS）
- **36氪机器人**: API 或 RSS
- **亿欧智库**: 专题报告

#### 行业垂直媒体（2个）
- **The Robot Report**: RSS
- **IEEE Spectrum Robotics**: RSS

#### 社交媒体/论坛（3个）
- **Reddit r/robotics**: PRAW 或 RSS
- **Twitter/X**: 关键账号监控（可选）
- **LinkedIn**: 公司页面更新（可选）

#### 学术资源（2个）
- **OpenReview**: CoRL/ICLR 机器人论文
- **会议网站**: ICRA/RSS RSS feeds

#### 公司官方（动态）
- 从 `companies.json` 读取公司列表
- 自动检测博客 RSS

### 插件化架构

**基础类设计**:
```python
class BaseSourceScraper:
    def __init__(self, config: Dict):
        self.config = config

    def scrape(self) -> List[NewsItem]:
        """返回标准化的新闻项列表"""
        raise NotImplementedError

    def is_relevant(self, item: NewsItem) -> bool:
        """判断是否相关"""
        return True
```

**实现示例**:
```python
class JiqizhixinScraper(BaseSourceScraper):
    def scrape(self) -> List[NewsItem]:
        feed = feedparser.parse(self.config['rss_url'])
        items = []
        for entry in feed.entries:
            if self.is_relevant(entry):
                items.append(self.parse_entry(entry))
        return items
```

**容错机制**:
- 每个源独立 try-catch
- 失败不影响其他源
- 记录失败日志到 `scraper.log`

## 4. 智能公司管理系统

### 三层公司列表

#### 1. companies.json（核心白名单）
```json
{
  "tier1": [
    {
      "name": "Figure AI",
      "aliases": ["figure", "figure robotics"],
      "priority": "high",
      "added_date": "2026-01-20",
      "blog_rss": "https://figure.ai/blog/rss"
    },
    {
      "name": "星海图",
      "aliases": ["星海图", "singhai", "XingHaiTu"],
      "priority": "high",
      "added_date": "2026-02-03"
    },
    {
      "name": "自变量",
      "aliases": ["自变量", "ziliang", "Autonomous Variable"],
      "priority": "high",
      "added_date": "2026-02-03"
    }
  ],
  "tier2": [
    {
      "name": "Agility Robotics",
      "aliases": ["agility"],
      "priority": "medium"
    }
  ]
}
```

#### 2. discovered_companies.json（自动发现）
```json
{
  "companies": [
    {
      "name": "XYZ Robotics",
      "first_seen": "2026-02-01",
      "occurrences": 3,
      "sources": [
        {
          "title": "XYZ Robotics raises $50M...",
          "url": "https://...",
          "source": "TechCrunch",
          "date": "2026-02-01"
        }
      ],
      "confidence": 0.85
    }
  ]
}
```

#### 3. review_queue.txt（待审核）
```markdown
# 待审核公司列表
# 指令：在公司名前添加 [x] 表示批准，[-] 表示拒绝

[ ] XYZ Robotics - 出现 3 次 - 首次: 2026-02-01
    信心度: 85%
    相关文章:
    - "XYZ Robotics raises $50M..." (TechCrunch, 2026-02-01)
    - "XYZ demos new gripper..." (Robot Report, 2026-02-02)

[ ] 具身智能科技 - 出现 2 次 - 首次: 2026-02-02
    信心度: 72%
    相关文章:
    - "具身智能科技发布新品..." (机器之心, 2026-02-02)
```

### 自动发现机制

**识别逻辑**:
1. 在抓取的文本中使用正则和 NLP 识别公司名
2. 过滤规则：
   - 必须出现在人形机器人/具身智能相关文章中
   - 名称符合公司命名规范
   - 不在已知公司列表中
3. 记录到 `discovered_companies.json`
4. 当出现次数 ≥ 2 时，添加到 `review_queue.txt`

**审核工具**:
```bash
python manage_companies.py
```

**流程**:
1. 读取 `review_queue.txt`
2. 逐个显示公司信息
3. 用户选择：添加到 tier1/tier2 或忽略
4. 自动更新 `companies.json`
5. 清空已处理的队列

### 运行时提醒

**在 `update.sh` 中**:
```bash
# 抓取数据后
python scraper.py

# 检查是否有新公司
if [ -s review_queue.txt ]; then
    echo "⚠️  发现 $(grep -c '^\[ \]' review_queue.txt) 家新公司待审核！"
    echo "   运行 'python manage_companies.py' 查看详情"
fi
```

## 5. AI 智能摘要生成

### 摘要维度

#### 1. 技术趋势分析 (🔬)
- 识别研究热点：多篇论文关注的共同方向
- 技术突破：新方法、新模型、性能提升
- 跨领域融合：AI + 机器人 + 其他技术

#### 2. 公司动态关联 (🏢)
- 公司之间的竞争关系
- 合作或收购动向
- 战略方向变化
- 人才流动

#### 3. 行业影响评估 (💡)
- 重大融资（金额、阶段、投资方）
- 产品发布（技术亮点、市场定位）
- 技术突破的商业化潜力
- 政策或市场变化

### 摘要生成流程

**update.sh 中的集成**:
```bash
#!/bin/bash
echo "🤖 开始更新具身智能追踪器..."

# 1. 抓取数据
echo "📊 抓取数据..."
python3 scraper.py

# 2. 检查新公司
if [ -s review_queue.txt ]; then
    echo "⚠️  发现新公司待审核！"
fi

# 3. 等待 Claude 分析
echo ""
echo "=========================================="
echo "📝 数据已更新，准备生成智能摘要"
echo "=========================================="
echo ""
echo "📋 今日数据概览："
python3 -c "import json; d=json.load(open('data.json')); print(f\"  - 论文: {len(d['data']['papers'])}篇\"); print(f\"  - 新闻: {len(d['data']['news'])}条\"); print(f\"  - 融资: {len(d['data']['funding'])}条\"); print(f\"  - 产品: {len(d['data']['products'])}条\")"
echo ""
echo "⏳ 等待 Claude 生成分析摘要..."
echo "   (在 Claude Code 中运行时，Claude 会自动分析并生成摘要)"
echo ""

# 等待用户确认或 Claude 完成（通过检查文件是否存在）
TODAY=$(date +%Y-%m-%d)
DIGEST_FILE="digests/${TODAY}-digest.md"

# 如果摘要文件不存在，等待
while [ ! -f "$DIGEST_FILE" ]; do
    sleep 2
done

echo "✅ 摘要生成完成！"
echo ""

# 4. 生成 HTML
echo "🎨 生成页面..."
python3 generator.py

# 5. 推送
echo "📤 推送到 GitHub..."
git add .
git commit -m "Update tracker data - $(date +%Y-%m-%d)"
git push

echo "✅ 更新完成！"
echo "🌐 访问: https://jzhu9324.github.io/Embodied-ai-tracker/"
```

### 摘要 Markdown 格式

**文件**: `digests/2026-02-03-digest.md`

```markdown
# 具身智能日报 - 2026-02-03

## 🔬 技术趋势分析

### 研究热点
- **双臂协作操作**: 今日 3 篇论文（CoFreeVLA, Multi-Modular MANTA-RAY, DynamicVLA）聚焦双臂协作，重点解决碰撞避免和动态物体抓取问题。这表明业界正在从单臂向双臂场景过渡，复杂操作能力成为关注焦点。

- **视觉-语言-动作模型演进**: DynamicVLA 和 AIR-VLA 分别针对动态物体和空中操作场景扩展 VLA 模型，说明 VLA 架构正在向更复杂场景泛化。

### 技术突破
- **GPU 加速训练**: mjlab 框架提供 GPU 加速的机器人学习环境，可能显著缩短训练时间，降低研究门槛。

- **空间机器人**: 针对太空环境的自适应抓取研究（Towards Space-Based Grasping），表明机器人技术正在拓展到极端环境。

## 🏢 公司动态关联

### 重点公司
- **Physical Intelligence**: TechCrunch 深度报道，Stripe 前高管 Lachy Groom 投资。作为"硅谷最热门的机器人大脑"，其技术路线和商业模式值得持续关注。

- **Anthropic**: 推出 Cowork 的 agentic 插件，强化 AI agent 能力。虽非直接机器人公司，但其技术可能赋能具身智能系统。

### 跨行业动态
- **Elon Musk 公司生态**: SpaceX、Tesla、xAI 传出合并谈判。若成真，将形成从 AI（xAI）到机器人（Optimus）再到应用场景（SpaceX、Tesla）的完整生态，可能改变行业格局。

## 💡 行业影响评估

### 重大事件
- **融资**: 本周期内无重大融资消息

### 技术影响
- **高影响**: mjlab 框架如获广泛采用，可能加速整个行业的研究进度
- **中等影响**: VLA 模型的场景扩展（动态物体、空中操作）推动技术边界
- **值得关注**: 双臂操作的研究密度上升，预示商业化需求增长

### 市场信号
- Physical Intelligence 持续获关注，表明"通用机器人大脑"方向获资本认可
- 学术界关注点从静态场景转向动态/复杂场景，符合商业化需求

---

📊 **数据统计**: 10 papers | 0 funding | 0 products | 5 news
🤖 **总计**: 15 items
⏰ **生成时间**: 2026-02-03 08:30:00
```

### Claude Code 集成方式

**用户操作**:
1. 在 Claude Code 中运行：`./update.sh`
2. 脚本运行到"等待 Claude 分析"时暂停
3. 我（Claude）自动读取 `data.json`
4. 生成上述格式的摘要，写入 `digests/YYYY-MM-DD-digest.md`
5. 脚本检测到文件存在，继续执行

**优势**:
- 本地运行，无需 API key
- 摘要质量高，深度分析
- 用户无感知，自动化流程

## 6. 前端展示改进

### generator.py 改进

**读取最新摘要**:
```python
def get_latest_digest():
    """从 digests/ 目录读取最新的摘要"""
    import glob
    digest_files = sorted(glob.glob('digests/*.md'), reverse=True)
    if digest_files:
        with open(digest_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
            return parse_digest_markdown(content)
    return None

def parse_digest_markdown(content: str) -> Dict:
    """解析 Markdown 摘要"""
    sections = {
        'tech_trends': [],
        'company_dynamics': [],
        'industry_impact': []
    }

    current_section = None
    current_content = []

    for line in content.split('\n'):
        if '## 🔬 技术趋势分析' in line:
            current_section = 'tech_trends'
        elif '## 🏢 公司动态关联' in line:
            if current_section and current_content:
                sections[current_section].append('\n'.join(current_content))
            current_section = 'company_dynamics'
            current_content = []
        elif '## 💡 行业影响评估' in line:
            if current_section and current_content:
                sections[current_section].append('\n'.join(current_content))
            current_section = 'industry_impact'
            current_content = []
        elif line.startswith('###') or line.startswith('-'):
            if current_section:
                current_content.append(line)

    if current_section and current_content:
        sections[current_section].append('\n'.join(current_content))

    return sections
```

### HTML 模板改进

**Today's Digest 部分**:
```html
<!-- 今日摘要 -->
<div class="digest">
    <div class="digest-title">TODAY'S DIGEST</div>

    <!-- 技术趋势 -->
    <div class="digest-section">
        <div class="digest-section-header">🔬 技术趋势分析</div>
        <div class="digest-section-content">
            {tech_trends_html}
        </div>
    </div>

    <!-- 公司动态 -->
    <div class="digest-section">
        <div class="digest-section-header">🏢 公司动态关联</div>
        <div class="digest-section-content">
            {company_dynamics_html}
        </div>
    </div>

    <!-- 行业影响 -->
    <div class="digest-section">
        <div class="digest-section-header">💡 行业影响评估</div>
        <div class="digest-section-content">
            {industry_impact_html}
        </div>
    </div>
</div>
```

### CSS 样式

```css
.digest-section {
    margin: 15px 0;
    padding: 12px;
    border-left: 3px solid #00ff00;
    background: rgba(0, 255, 0, 0.03);
}

.digest-section-header {
    font-size: 14px;
    font-weight: bold;
    color: #00ff00;
    margin-bottom: 8px;
}

.digest-section-content {
    font-size: 13px;
    line-height: 1.7;
    color: #ffb000;
}

.digest-section-content h3 {
    color: #ffcc00;
    font-size: 13px;
    margin: 10px 0 5px 0;
}

.digest-section-content ul {
    margin: 5px 0;
    padding-left: 20px;
}

.digest-section-content li {
    margin: 5px 0;
}
```

## 7. 自动化和部署

### GitHub Actions 配置

**时间设置**: 每天早上 7-9 点（北京时间）
- UTC 时间: 23:00-01:00（前一天晚上）
- Cron: `0 23 * * *` 或 `0 0 * * *`

**workflow 文件**: `.github/workflows/daily-update.yml`

```yaml
name: Daily Update

on:
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00 = 北京时间 07:00
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run scraper
        run: |
          python scraper.py

      - name: Generate AI Digest (TODO: 需要配置 API)
        run: |
          echo "⚠️  AI 摘要生成需要 Anthropic API"
          echo "暂时跳过，使用本地生成的摘要"
          # 未来实现：python generate_digest.py

      - name: Generate HTML
        run: |
          python generator.py

      - name: Check for company review
        run: |
          if [ -s review_queue.txt ]; then
            echo "⚠️  发现新公司待审核"
            cat review_queue.txt
          fi

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v7
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: Update tracker data
          title: '[Auto] Daily Tracker Update'
          body: |
            自动更新具身智能追踪器数据

            📊 Items: ${{ steps.get-count.outputs.count || 'N/A' }}
            🕐 Updated: ${{ github.event.head_commit.timestamp }}

            ⚠️  注意：如果有新公司待审核，请查看 review_queue.txt
          branch: auto-update
          delete-branch: true
          draft: false
```

**注意事项**:
- GitHub Actions 环境无法直接使用 Claude Code
- 需要配置 Anthropic API key 或使用降级方案（简单统计摘要）
- 优先保证本地流程完善

### 本地流程（优先实现）

**update.sh**:
```bash
#!/bin/bash
set -e

echo "🤖 具身智能追踪器 - 每日更新"
echo "========================================"
echo ""

# 1. 数据抓取
echo "📊 步骤 1/4: 抓取数据..."
python3 scraper.py
echo ""

# 2. 检查新公司
if [ -s review_queue.txt ]; then
    NEW_COMPANIES=$(grep -c '^\[ \]' review_queue.txt)
    echo "⚠️  发现 ${NEW_COMPANIES} 家新公司待审核！"
    echo "   运行 'python manage_companies.py' 查看详情"
    echo ""
fi

# 3. AI 摘要生成
echo "📝 步骤 2/4: 生成智能摘要..."
echo "=========================================="
TODAY=$(date +%Y-%m-%d)
DIGEST_FILE="digests/${TODAY}-digest.md"

# 显示数据概览
python3 -c "
import json
d = json.load(open('data.json'))
print(f'📋 今日数据概览：')
print(f'  - 论文: {len(d[\"data\"][\"papers\"])} 篇')
print(f'  - 新闻: {len(d[\"data\"][\"news\"])} 条')
print(f'  - 融资: {len(d[\"data\"][\"funding\"])} 条')
print(f'  - 产品: {len(d[\"data\"][\"products\"])} 条')
"
echo ""
echo "⏳ 等待 Claude 分析并生成摘要..."
echo "   (Claude 会读取 data.json 并生成 ${DIGEST_FILE})"
echo ""

# 等待摘要文件生成（轮询检查）
WAIT_COUNT=0
MAX_WAIT=60  # 最多等待 60 秒
while [ ! -f "$DIGEST_FILE" ] && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ -f "$DIGEST_FILE" ]; then
    echo "✅ 摘要生成完成！"
else
    echo "⚠️  摘要文件未生成，将使用默认摘要"
fi
echo ""

# 4. 生成 HTML
echo "🎨 步骤 3/4: 生成页面..."
python3 generator.py
echo ""

# 5. Git 推送
echo "📤 步骤 4/4: 推送到 GitHub..."
git add .
git commit -m "Update tracker data - ${TODAY}" || echo "无更新内容"
git push
echo ""

echo "=========================================="
echo "✅ 更新完成！"
echo "🌐 访问: https://jzhu9324.github.io/Embodied-ai-tracker/"
echo "=========================================="
```

## 8. 实施计划

### Phase 1: 基础架构重构（优先级：高）

**时间**: 1-2 天

**任务**:
1. 创建 `sources/` 目录结构
2. 实现 `BaseSourceScraper` 基类
3. 重构现有 scraper（arXiv, HN, TechCrunch）为插件
4. 创建 `companies.json` 初始数据
5. 实现 `manage_companies.py` 基础功能

**验收标准**:
- scraper.py 使用新架构运行成功
- 可以通过配置添加/移除数据源
- 公司管理工具可以手动添加公司

### Phase 2: 数据源扩展（优先级：高）

**时间**: 2-3 天

**任务**:
1. 实现中文媒体源
   - 机器之心 RSS (`sources/jiqizhixin.py`)
   - 量子位网页抓取 (`sources/qbitai.py`)
   - 36氪 API (`sources/36kr.py`)
2. 实现社交平台源
   - Reddit (`sources/reddit.py`)
3. 实现学术源
   - OpenReview (`sources/openreview.py`)
4. 实现公司博客监控
   - 从 `companies.json` 读取 RSS
5. 测试各数据源稳定性和质量

**验收标准**:
- 每个新数据源独立可运行
- 容错机制生效（单个源失败不影响整体）
- 数据质量符合预期（相关性 > 80%）

### Phase 3: 公司自动发现（优先级：中）

**时间**: 1 天

**任务**:
1. 实现公司名识别逻辑
2. 创建 `discovered_companies.json` 管理
3. 实现审核队列生成 (`review_queue.txt`)
4. 完善 `manage_companies.py` 审核流程
5. 在 `update.sh` 中添加提醒

**验收标准**:
- 能够从文本中识别新公司（准确率 > 70%）
- 审核流程流畅（可以批量处理）
- 运行时智能提醒生效

### Phase 4: AI 智能摘要（优先级：高）

**时间**: 1 天

**任务**:
1. 创建 `digests/` 目录
2. 设计 Markdown 摘要模板
3. 改进 `update.sh`，集成等待机制
4. 测试 Claude Code 分析流程
5. 编写摘要生成指南（供 Claude 参考）

**验收标准**:
- `update.sh` 运行流畅，等待机制正常
- 生成的摘要包含三个维度分析
- 摘要质量高，有深度洞察

### Phase 5: 前端优化（优先级：中）

**时间**: 1 天

**任务**:
1. 修改 `generator.py` 读取和解析摘要
2. 更新 HTML 模板，展示新摘要格式
3. 优化 CSS 样式，适配摘要内容
4. 测试响应式布局
5. 修复 Tab 切换问题（已完成）

**验收标准**:
- 摘要在前端正确展示
- 三个维度清晰可读
- 移动端显示正常

### Phase 6: 测试和优化（优先级：中）

**时间**: 1 天

**任务**:
1. 端到端测试完整流程
2. 性能优化（减少抓取时间）
3. 错误处理完善
4. 文档更新（README, 使用说明）
5. GitHub Actions 修复（可选）

**验收标准**:
- 完整流程无错误运行
- 数据抓取 < 5 分钟
- README 完整准确

## 9. 技术细节

### 依赖包更新

**requirements.txt 新增**:
```
# 现有
requests==2.31.0
feedparser==6.0.10
beautifulsoup4==4.12.2
python-dateutil==2.8.2
anthropic==0.18.1

# 新增
praw==7.7.1              # Reddit
tweepy==4.14.0           # Twitter (可选)
openreview-py==1.30.0    # OpenReview
selenium==4.15.0         # 网页抓取 (可选)
```

### 配置文件结构

**config.json**:
```json
{
  "sources": {
    "arxiv": {"enabled": true, "max_results": 10},
    "hackernews": {"enabled": true, "max_results": 5},
    "techcrunch": {"enabled": true, "max_results": 5},
    "jiqizhixin": {"enabled": true, "rss_url": "https://..."},
    "reddit": {"enabled": true, "subreddit": "robotics"}
  },
  "filters": {
    "days_cutoff": 7,
    "min_relevance_score": 0.6
  },
  "update_schedule": {
    "time": "07:00",
    "timezone": "Asia/Shanghai"
  }
}
```

### 错误处理策略

1. **数据源失败**: 记录日志，继续其他源
2. **公司识别错误**: 保守策略，宁缺毋滥
3. **摘要生成失败**: 使用降级方案（简单统计）
4. **Git 推送失败**: 保留本地数据，发送通知

### 性能优化

1. **并发抓取**: 使用 `concurrent.futures` 并发抓取多个源
2. **缓存机制**: 对不常变化的数据（如公司博客列表）使用缓存
3. **增量更新**: 只抓取新数据，避免重复
4. **智能限流**: 根据源的限制动态调整请求频率

## 10. 风险和缓解

### 风险识别

1. **数据源不稳定**: RSS 失效、API 变更、反爬虫
   - 缓解：容错机制、定期检查、多源冗余

2. **AI 摘要质量**: 可能产生幻觉或不准确分析
   - 缓解：添加置信度标注、人工审核机制

3. **公司自动发现误报**: 识别出错误的公司名
   - 缓解：人工审核环节、提高识别阈值

4. **性能问题**: 数据源增多导致抓取时间过长
   - 缓解：并发、超时控制、可配置的源开关

5. **GitHub Actions 限制**: 运行时间、频率限制
   - 缓解：优化执行时间、考虑其他 CI 平台

### 降级方案

1. **摘要生成失败**: 使用简单统计摘要
2. **部分源失败**: 使用可用源的数据
3. **完全失败**: 保留上一次的数据和摘要

## 11. 后续迭代方向

### V2.0 功能
- 数据可视化（趋势图、公司关系图）
- 邮件/消息推送订阅
- 多语言支持（中英切换）
- 移动端 App

### V3.0 功能
- 用户自定义关注公司/关键词
- 历史数据分析和对比
- AI 对话式查询（"最近 Figure AI 有什么动态？"）
- 社区功能（评论、分享）

---

## 附录

### A. 文件清单

```
embodied-ai-tracker/
├── docs/
│   └── plans/
│       └── 2026-02-03-tracker-enhancement-design.md
├── sources/
│   ├── base.py
│   ├── arxiv.py
│   ├── hackernews.py
│   ├── techcrunch.py
│   ├── jiqizhixin.py
│   ├── qbitai.py
│   ├── 36kr.py
│   ├── reddit.py
│   ├── openreview.py
│   └── robot_report.py
├── digests/
│   └── 2026-02-03-digest.md
├── scraper.py
├── generator.py
├── manage_companies.py
├── companies.json
├── discovered_companies.json
├── review_queue.txt
├── config.json
├── update.sh
├── data.json
├── index.html
├── requirements.txt
└── README.md
```

### B. 关键命令

```bash
# 完整更新流程
./update.sh

# 只抓取数据
python scraper.py

# 只生成 HTML
python generator.py

# 审核新公司
python manage_companies.py

# 手动添加公司
python manage_companies.py add "星海图" --aliases "singhai,XingHaiTu"
```

### C. 参考资源

- arXiv API: https://arxiv.org/help/api
- Reddit PRAW: https://praw.readthedocs.io/
- OpenReview API: https://docs.openreview.net/
- Feedparser: https://feedparser.readthedocs.io/

---

**最后更新**: 2026-02-03
**状态**: ✅ 设计完成，待实施
