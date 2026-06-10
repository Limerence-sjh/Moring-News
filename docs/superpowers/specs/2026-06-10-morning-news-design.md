# Morning News — 设计文档

> 日期: 2026-06-10
> 状态: 已确认，待实现

## 1. 问题重构

用户说的是「想每天定时获取关注的信息并推送」，但真正的痛点是三类：

| 痛点 | 类型 | 对应信息源 |
|------|------|-----------|
| 信息焦虑 | 每天花大量时间在各平台「巡逻」，怕漏信息 | 所有源 |
| 信息错过 | 有需要及时响应的信息，没第一时间发现 | B站开播、指南针阈值 |
| 信息碎片化 | 信息散落各处，零散地看太累 | 微博/知乎/GitHub |

**核心定位**: 即时告警为主，每日摘要为辅的个人信息聚合推送工具。

## 2. 隐含需求

### 用户没提但未来会后悔没考虑的点

- **指南针数据获取方式未确定**: 这是最大的不确定性，如果数据拿不到，阈值告警就是空谈
- **微信推送的条数限制**: Server酱免费版每天5条，需要额度管理策略
- **历史数据积累的价值**: 指南针指标的历史趋势只有积累数据后才能看到
- **信息源网站反爬/改版风险**: 各平台随时可能改版，需要容错机制
- **小圈分享时多用户推送**: 当前是个人工具，但需要为多用户预留架构

### 规模化后的约束

- 微博/知乎热榜爬取需要处理反爬机制（频率限制、验证码）
- 多用户场景下推送条数会指数增长，Server酱额度可能不够
- 指南针数据如果只能手动获取，多用户场景下无法自动化

## 3. MVP 范围

### 必须做的 (Phase 1)

| 源 | 功能 | 时效类型 |
|----|------|---------|
| B站UP主 | 开播即时通知 + 每5分钟采集标题存入数据库 | 即时 |
| GitHub Trending | 涨星最快前10项目 | 每日 |
| 微博热搜 | Top5/10热搜列表 | 每日 |

### Phase 2

| 源 | 功能 | 备注 |
|----|------|------|
| 指南针活跃市值 | 阈值告警(-2.3%, 4%) + 收盘值 | 先研究数据获取方式，可能需手动录入兜底 |

### Phase 3

| 源/功能 | 功能 | 备注 |
|---------|------|------|
| 知乎热榜 | 前10热点 | 优先级最低 |
| 多用户支持 | per-user配置 + 推送按用户分发 | 小圈分享 |

### 可以砍掉的

- 语义筛选/关键词过滤（B站直播间标题只做采集存储，不做即时内容筛选推送）
- 桌面可视化界面（纯后台服务 + 推送即可）
- 多渠道并行推送（微信优先，邮件降级，不做钉钉/飞书/Telegram）

## 4. 成功指标

| 指标 | 衡量方式 | 目标 |
|------|---------|------|
| B站开播通知及时性 | 从UP主开播到收到微信推送的延迟 | ≤5分钟 |
| 每日摘要完整性 | 18:00推送是否包含所有enabled源的数据 | 100%覆盖 |
| 推送可靠性 | 微信推送成功率 | ≥95%，失败时邮件降级 |
| 指南针阈值告警准确性 | 触发阈值时是否收到通知 | Phase 2目标 |
| 系统稳定性 | 连续运行天数 | ≥30天无手动干预 |

## 5. 风险

| 风险 | 可能原因 | 应对策略 |
|------|---------|---------|
| 指南针数据无法自动获取 | 无公开API、桌面客户端数据难以提取 | 设计手动录入兜底方案 |
| Server酱推送额度不足 | 多UP主开播+阈值触发+摘要同天 | urgent优先占额度，daily降级邮件 |
| 信息源反爬/改版 | 微博/知乎更新页面结构 | 插件独立，单源崩溃不影响其他 |
| 服务器断电断网 | 本地/云服务器不稳定 | APScheduler jobstore持久化，重启自动恢复 |
| 推送噪音过大 | 每日摘要太长或即时告警太频繁 | 18:00合并推送，即时告警仅开播/阈值触发 |

## 6. 架构设计

### 6.1 整体架构

```
┌─────────────────────────────────────────┐
│              Morning News                │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ B站插件  │  │指南针插件│  │微博插件  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
│       │            │            │       │
│       ▼            ▼            ▼       │
│  ┌──────────────────────────────────┐   │
│  │         调度器 APScheduler        │   │
│  │  即时源: 每5分钟轮询              │   │
│  │  每日源: 每天18:00汇总            │   │
│  └──────────────┬───────────────────┘   │
│                  │                       │
│                  ▼                       │
│  ┌──────────────────────────────────┐   │
│  │           推送层 Pusher           │   │
│  │  Server酱 → 微信（主）            │   │
│  │  SMTP     → 適件（备）            │   │
│  └──────────────┬───────────────────┘   │
│                  │                       │
│  ┌──────────────────────────────────┐   │
│  │         数据持久化 SQLite         │   │
│  │  记录历史值、阈值触发、推送日志    │   │
│  └──────────────────────────────────┘   │
│                                         │
│  config.yaml ── 所有配置项              │
│  (关注的UP主ID、阈值、推送key等)       │
└─────────────────────────────────────────┘
```

**核心设计原则**:

1. **插件隔离**: 每个信息源是独立的 Python 文件，互不干扰
2. **配置驱动**: 所有关注项、阈值、推送渠道都在 config.yaml
3. **状态持久化**: SQLite 存历史数据
4. **推送抽象**: Pusher 层屏蔽微信/邮件差异，插件不需要知道推给了谁

### 6.2 插件系统

每个信息源是一个 Python 文件，放在 `plugins/` 目录下，遵循统一接口:

```python
# plugins/bilibili_live.py（示例骨架）

class BilibiliLivePlugin:
    """B站UP主开播通知+标题采集"""

    name = "bilibili_live"
    schedule_type = "interval"     # interval=周期轮询 | cron=定时汇总
    interval_minutes = 5           # 轮询间隔

    def __init__(self, config):
        """从 config.yaml 读取本插件的配置"""
        self.up_ids = config["bilibili"]["up_ids"]

    def run(self, db):
        """
        被调度器调用，执行一次采集

        db: SQLite 数据库对象，用于:
           - 读取上次状态
           - 写入本次采集数据
           - 返回需要推送的消息列表

        返回: list[Message]
        """
        messages = []
        for up_id in self.up_ids:
            was_live = db.get_last_status(up_id)
            is_live, title = self._fetch_status(up_id)

            if not was_live and is_live:
                messages.append(Message(
                    title=f"🔴 {db.get_up_name(up_id)} 开播了",
                    content=f"直播间标题: {title}",
                    level="urgent"
                ))

            db.save_live_record(up_id, title, is_live)

        return messages
```

**插件接口约定**:

| 属性/方法 | 用途 | 必须实现 |
|----------|------|---------|
| `__init__(config)` | 读取配置 | ✓ |
| `run(db)` | 执行采集，返回推送消息 | ✓ |
| `name` | 插件标识 | ✓ |
| `schedule_type` | interval / cron | ✓ |
| `interval_minutes` | 轮询间隔(interval类型) | ✓ |
| `cron_expression` | cron表达式(cron类型) | interval类型不需要 |

**即时插件 vs 每日插件**:

| | 即时插件 | 每日插件 |
|--|---------|---------|
| 调度方式 | 每5分钟轮询 | 每天18:00执行一次 |
| 返回消息 | 有事件才推 | 总是返回当日摘要 |
| 数据用途 | 即时告警 + 存历史 | 只存历史，汇总推送 |

**加新源流程**:

1. 在 `plugins/` 下新建 `.py` 文件
2. 实现上述接口
3. 在 `config.yaml` 中加一段配置
4. 重启服务 → 调度器自动发现并加载

### 6.3 推送层

**推送策略**:

| 场景 | 行为 |
|------|------|
| 即时告警(level=urgent) | 立刻推 Server酱 → 微信；失败则降级邮件 |
| 每日摘要(level=daily) | 每天18:00合并所有每日源 → 一条长消息推送 |
| Server酱推送失败 | 自动降级到邮件 |
| Server酱限流 | urgent优先占额度；daily合并为一条节省额度 |

**Server酱限制**:

- 免费版: 每天5条消息上限
- 付费版(~50元/年): 每天数十条
- 消息格式: 支持 Markdown

**每日消息量预估**:

- 即时告警: 0~3条
- 每日摘要: 1条
- 总计: 1~4条/天，免费版可覆盖

**每日摘要格式** (18:00推送):

```
📰 Morning News 每日摘要 | 2026-06-10

🔴 B站直播
  UP主A: 14:30开播「xxx」，16:00关播
  标题变化:
    14:30 「聊天」
    15:00 「连麦答疑」

📊 指南针活跃市值
  收盘值: 2.1%，未触发阈值

🔥 微博热搜
  1. xxx
  2. xxx
  3. xxx
  4. xxx
  5. xxx

🚀 GitHub Trending
  1. repo-name (+320⭐)
  2. repo-name (+280⭐)
  3. ...

📌 知乎热榜
  1. xxx
  2. xxx
  3. ...
```

> TopX 列式排列，不压缩到一行。

**推送日志** (SQLite):

| 字段 | 说明 |
|------|------|
| timestamp | 推送时间 |
| channel | serverchan / email |
| level | urgent / daily |
| source | 插件名 |
| title | 消息标题 |
| content | 消息正文 |
| success | 是否推送成功 |

### 6.4 配置设计 (config.yaml)

```yaml
# Morning News 配置文件

# 推送渠道
push:
  serverchan:
    sendkey: "your-sendkey-here"
    daily_limit: 5
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 465
    from: "your-email@gmail.com"
    password: "your-password"
    to: "target-email@gmail.com"

# 调度配置
scheduler:
  instant_interval: 5    # 即时源轮询间隔(分钟)
  daily_time: "18:00"    # 每日摘要推送时间

# 信息源配置
sources:
  bilibili_live:
    enabled: true
    up_ids:
      - "12345"
      - "67890"

  zhinanzen:
    enabled: true
    thresholds:
      - -2.3
      - 4.0
    daily_snapshot: true

  weibo:
    enabled: true
    top_count: 5

  github_trending:
    enabled: true
    top_count: 10
    language: ""
    since: "daily"

  zhihu:
    enabled: true
    top_count: 10
```

### 6.5 数据持久化 (SQLite)

```sql
-- 推送日志
CREATE TABLE push_log (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME,
  channel TEXT,
  level TEXT,
  source TEXT,
  title TEXT,
  content TEXT,
  success BOOLEAN
);

-- 指南针历史数据
CREATE TABLE zhinanzen_history (
  id INTEGER PRIMARY KEY,
  date DATE,
  value REAL,
  timestamp DATETIME
);
```

选择 SQLite 的理由: 个人工具零运维，文件级数据库，未来迁移 PostgreSQL 无门槛。

### 6.6 容错机制

| 场景 | 处理方式 |
|------|---------|
| 信息源网站改版/反爬 | 插件抛出 SourceError，跳过本次采集，写入错误日志，不推空消息 |
| Server酱推送失败 | 自动降级到邮件 |
| 服务器断网重启 | APScheduler jobstore=SQLite持久化，重启自动恢复 |
| 指南针数据获取失败 | 连续失败3天 → 推送「数据源异常」告警 |
| 单个插件崩溃 | 独立运行，一个崩溃不影响其他，异常被调度器捕获 |

### 6.7 MVP 里程碑

**Phase 1** — 确定性最高的源:

| 源 | 原因 |
|----|------|
| B站开播通知 | 数据确定可获取，验证即时告警+推送链路 |
| GitHub Trending | 数据确定可获取，验证每日摘要流程 |
| 微博热搜 | 数据确定可获取 |

> Phase 1 完成标志: 稳定收到B站开播微信通知 + 每日摘要微信推送

**Phase 2** — 研究指南针接入:

| 源 | 备注 |
|----|------|
| 指南针活跃市值 | 先研究数据获取方式；如无法自动获取 → 手动录入兜底 |

**Phase 3** — 补齐 + 小圈扩展:

| 源/功能 | 备注 |
|---------|------|
| 知乎热榜 | 优先级最低 |
| 多用户支持 | config.yaml拆分为per-user配置 |