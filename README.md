# 🎯 OpenClaw Job Hunter Skill

> **自动化求职助手** — 基于 [OpenClaw](https://github.com/openclaw/openclaw) 智能体框架

每天自动从多个渠道采集招聘/内推信息，AI 匹配打分后推送到飞书多维表格。

当前内置渠道针对中国大陆求职市场，但 Skill 结构可灵活扩展到其他地区和渠道。

## ✨ 特性

- 🔍 **多渠道覆盖**：BOSS直聘、小红书、微信公众号、牛客、力扣、V2EX、掘金、LinuxDO + 自由搜索
- 🤖 **智能策略**：根据渠道特性自动选择最佳采集方式（web_search / web_fetch / browser）
- 📊 **三层去重**：本地缓存 → 飞书历史 → AI 匹配打分，避免重复推送
- ⏰ **每日定时**：通过 OpenClaw cron 自动执行
- 📋 **飞书推送**：结果自动写入飞书多维表格，支持移动端查看
- 🕐 **时间优先**：优先采集当日最新发布的岗位信息
- 🔧 **可自定义**：渠道策略、搜索关键词、偏好、表格 schema 均可按需修改

## 📁 目录结构

```
job-hunter/
├── SKILL.md              # Skill 核心定义（Prompt + 策略 + 流程）
├── references/
│   ├── job-profile.md    # 求职偏好配置（城市、薪资、公司类型等）
│   └── resume.md         # 简历信息（在线简历 URL 或内容）
├── scripts/
│   └── cache_manager.py  # URL 去重缓存管理器（SQLite）
└── data/
    └── crawl_cache.db    # 自动生成的爬取缓存（gitignored）
```

## 🚀 快速开始

### 前置条件

- [OpenClaw](https://github.com/openclaw/openclaw) 已安装并配置
- 飞书机器人已配置（需要多维表格读写权限）
- 浏览器工具已启用（`browser.enabled: true`）
- Brave Search API Key 已配置（用于 `web_search`）

### 安装

1. **克隆到 OpenClaw Skills 目录**：

```bash
# 方式一：放到全局 Skills 目录
git clone https://github.com/boat2moon/openclaw-job-hunter.git ~/.openclaw/skills/job-hunter

# 方式二：放到自定义目录，通过 openclaw.json 配置 extraDirs
git clone https://github.com/boat2moon/openclaw-job-hunter.git /your/path/skills/job-hunter
```

如果使用方式二，在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "skills": {
    "load": {
      "extraDirs": ["/your/path/skills"]
    }
  }
}
```

2. **配置求职偏好**：编辑 `references/job-profile.md`，填入你的偏好（城市、薪资、公司类型等）。

3. **配置简历**：编辑 `references/resume.md`，放入你的简历内容或在线简历 URL。

4. **配置飞书表格**：在 `SKILL.md` 中将 `YOUR_APP_TOKEN` 和 `YOUR_TABLE_ID` 替换为你自己的飞书多维表格 ID。

5. **重启 OpenClaw Gateway** 并对话触发：

```
> 帮我找一下最新的招聘岗位
```

或使用斜杠命令：`/job-hunter`

## 📡 渠道策略

| 类别 | 渠道 | 采集方式 | 说明 |
|------|------|---------|------|
| 求职平台 | BOSS直聘 | `web_search` | 反爬严格，只通过搜索引擎 |
| 社媒 | 小红书 | `browser` | 需登录，SPA 动态页面 |
| 社媒 | 微信公众号 | `browser` | 搜狗微信搜索 |
| 社区 | 牛客/力扣/V2EX/掘金/LinuxDO | `browser` | 统一浏览器，稳定处理翻页 |
| 补充 | 自由搜索 | `web_search` + `web_fetch` | 公司官网、内推信息等 |

> 可根据自身需求在 `SKILL.md` 中增删渠道，添加新的 URL 模板即可。

## 🔧 Clash 代理用户

如果你使用 Clash/Clash Verge 的 TUN 模式（Fake IP），`web_fetch` 可能会因为 SSRF 保护拦截 198.18.x.x 地址。解决方案：

```json
{
  "tools": {
    "web": {
      "fetch": {
        "ssrfPolicy": {
          "allowRfc2544BenchmarkRange": true
        }
      }
    }
  }
}
```

相关 PR：[openclaw/openclaw#40354](https://github.com/openclaw/openclaw/pull/40354)

## 📄 License

MIT
