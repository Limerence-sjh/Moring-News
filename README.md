# Morning News 📰

个人信息聚合推送工具 —— 每天定时获取全网关注的信息，推送到微信/邮件。

## 功能

| Phase | 功能 | 状态 |
|-------|------|------|
| Phase 1 | B站开播 + GitHub Trending + 微博热搜 | ✅ 完成 |
| Phase 2 | 指南针活跃市值阈值告警 | ⏳ 待研究 |
| Phase 3 | 知乎热榜 + 多用户支持 | ⏳ 计划中 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 编辑配置
cp config.example.yaml config.yaml
# 填入你的 Server酱 SendKey 和其他配置

# 初始化数据库
python -m morning_news --initdb

# 测试运行(只跑一次，不启动调度)
python -m morning_news --dry-run

# 正常启动(后台调度)
python -m morning_news --config config.yaml
```

## CLI 选项

| 选项 | 说明 |
|------|------|
| `--config PATH` | 配置文件路径 (默认: config.yaml) |
| `--initdb` | 初始化数据库后退出 |
| `--dry-run` | 运行所有插件一次后退出 (不启动调度) |
| `--verbose` | 启用 DEBUG 级别日志 |

## 推送渠道

Morning News 支持多推送渠道，按优先级尝试，失败时自动降级到下一渠道:

1. **Server酱** → 微信推送 (需要 SendKey，免费版每日5条上限)
2. **Email** → SMTP邮件推送 (作为降级备用渠道)

- `urgent` 级别消息 (如开播通知): 立即推送，Server酱优先
- `daily` 级别消息 (如每日摘要): 合并推送，受 Server酱每日上限限制

## 添加新的信息源

5 步添加自定义信息源:

1. 在 `morning_news/plugins/` 下复制 `template.py` 并重命名
2. 继承 `BasePlugin`，设置 `name` 和 `schedule_type`
3. 实现 `run(db) → PluginResult` 方法 (参考 template.py 注释)
4. 在 `config.yaml` 的 `sources` 下添加配置段
5. 重启服务即可自动加载

最小代码示例:

```python
from morning_news.plugins.base import BasePlugin
from morning_news.models import Message, PluginResult

class MyPlugin(BasePlugin):
    name = "my_source"
    schedule_type = "cron"  # 或 "interval"

    def run(self, db) -> PluginResult:
        data = fetch_my_data()
        messages = [Message(title=d["title"], content=d["desc"], level="daily", source=self.name) for d in data]
        return PluginResult(messages=messages, data={"count": len(data)})
```

## 项目结构

```
morning_news/
├── __init__.py
├── __main__.py            # python -m morning_news 入口
├── main.py                # CLI 入口，argparse
├── config_loader.py       # 配置加载与验证
├── scheduler.py           # APScheduler 调度
├── db.py                  # SQLite 数据库操作
├── models.py              # Message / PluginResult 数据模型
├── pusher/                # 推送模块
│   ├── serverchan.py      # Server酱 (微信)
│   ├── email.py           # SMTP 邮件
│   └── manager.py         # 推送管理 (优先级 + 降级)
├── plugins/               # 信息源插件
│   ├── base.py            # 插件基类
│   ├── bilibili_live.py   # B站UP主开播通知
│   ├── github_trending.py # GitHub Trending
│   ├── weibo.py           # 微博热搜
│   └── template.py        # 新插件模板
config.yaml                # 用户配置
config.example.yaml        # 配置示例
tests/                     # 测试
data/                      # 数据库文件 (gitignored)
logs/                      # 日志文件 (gitignored)
```

## 开发

```bash
# 运行测试
pytest tests/

# 启用详细日志
python -m morning_news --verbose --dry-run
```

## License

MIT