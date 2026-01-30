#!/bin/bash
# 具身智能追踪器 - 一键更新脚本

cd ~/embodied-ai-tracker

echo "🤖 开始更新具身智能追踪器..."

# 运行爬虫
echo "📊 爬取数据..."
python3 scraper.py

# 生成HTML
echo "🎨 生成页面..."
python3 generator.py

# 推送到GitHub
echo "📤 推送到GitHub..."
git add .
git commit -m "Update tracker data"
git push

echo "✅ 更新完成！"
echo "🌐 访问: https://jzhu9324.github.io/embodied-ai-tracker/"
