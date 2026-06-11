# Morning News 📰

个人信息聚合推送工具 —— 每天定时获取全网关注的信息，推送到微信/邮件。

## 功能

- 🔴 B站UP主开播即时通知
- 🚀 GitHub Trending 每日摘要
- 🔥 微博热搜每日摘要
- 📌 知乎热榜每日摘要 (Phase 3)
- 📊 指南针活跃市值阈值告警 (Phase 2)

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 编辑配置
cp config.example.yaml config.yaml
# 填入你的 Server酱 SendKey 和其他配置

# 初始化数据库
python -m morning_news --initdb

# 启动服务
python -m morning_news --config config.yaml

# 测试运行(只跑一次，不启动调度)
python -m morning_news --dry-run
```

## 配置说明

见 `config.example.yaml`

## 添加新的信息源

1. 在 `morning_news/plugins/` 下创建新的 `.py` 文件
2. 继承 `BasePlugin`，实现 `run()` 方法
3. 在 `config.yaml` 的 `sources` 下添加配置段
4. 重启服务

## 开发状态

| Phase | 功能 | 状态 |
|-------|------|------|
| Phase 1 | B站+GitHub+微博 | 🚧 开发中 |
| Phase 2 | 指南针活跃市值 | ⏳ 待研究 |
| Phase 3 | 知乎+多用户 | ⏳ 计划中 |

## 项目结构

```
morning_news/
├── __init__.py
├── main.py              # 入口，CLI
├── config_loader.py     # 配置加载与验证
├── scheduler.py         # APScheduler 调度
├── db.py                # SQLite 数据库操作
├── models.py            # Message/PluginResult 数据模型
├── pusher/              # 推送模块
│   ├── serverchan.py    # Server酱(微信)
│   ├── email.py         # SMTP邮件
│   └── manager.py       # 推送管理(优先级+降级)
├── plugins/             # 信息源插件
│   ├── base.py          # 插件基类
│   ├── bilibili_live.py # B站UP主开播
│   ├── github_trending.py # GitHub Trending
│   ├── weibo.py         # 微博热搜
│   └── template.py      # 新插件模板
config.yaml              # 用户配置
tests/                   # 测试
data/                    # 数据库文件(gitignored)
logs/                    # 日志文件(gitignored)
```