---
name: job-hunter
description: |
  自动化求职助手。每天自动从多个渠道采集招聘/内推信息，AI 匹配打分后推送到飞书多维表格。
  触发条件：用户提到找工作、求职、招聘、投简历、内推、校招、秋招、春招等。
---

# 求职助手（job-hunter）

## 运行环境

- 如运行 **Clash Verge TUN 模式**（全局代理），需配置 `ssrfPolicy`（见 README）
- `browser` 需提前手动登录各平台（BOSS 除外），保持登录态
- `browser` 无需登录：微信文章（搜狗）
- LinuxDO 受 Cloudflare 防护，首次可能需手动通过验证

## 可用工具

| 工具 | 用途 |
|---|---|
| `web_search` | 搜索引擎检索（Brave Search） |
| `web_fetch` | 轻量抓取静态页面内容 |
| `browser` navigate + snapshot | 浏览器抓取（动态页面/需登录/需交互） |
| `feishu_bitable_*` | 读写飞书多维表格 |
| `cron` | 定时任务管理 |
| `exec` | 运行本地脚本 |

## 各渠道采集策略

> **时间优先原则**：所有渠道优先采集最新发布的内容。搜索时尽量按时间排序/过滤，确保当日新发布的岗位优先被发现。因为每日都重复执行，历史遗漏的概率可能会随时间递减。

### 🔍 BOSS直聘（web_search only）

**⚠️ BOSS 反爬极其严格，禁止使用 browser（会自动关闭标签页）！**

- 只通过 `web_search` 搜索：`site:zhipin.com <关键词> <城市>`（自动带近期时间过滤）
- 从搜索结果摘要中提取岗位信息（标题、公司、薪资、链接）
- 不要尝试打开 zhipin.com 的任何页面

### 🌐 社媒渠道（browser）

**小红书**（需登录态）
1. `browser` navigate → `https://www.xiaohongshu.com/search_result?keyword=<关键词>&type=1`
2. 等待 3-5 秒 → `browser` snapshot → 提取帖子列表
3. 对感兴趣的帖子 → 点击进入 → snapshot 获取详情

**微信文章公众号**（搜狗微信文章搜索）
1. `browser` navigate → `https://weixin.sogou.com/weixin?type=2&s_from=input&query=<关键词>校招`（默认按时间排序）
2. snapshot → 提取文章列表和链接
3. 对感兴趣的文章 → navigate 打开 → snapshot 获取正文

### 🌐 社区渠道（browser）

> 社区类网站虽然部分支持 web_fetch，但为了稳定处理翻页、排序、动态内容，**统一使用 browser**。

**牛客**
- `browser` navigate → `https://www.nowcoder.com/search/all?type=all&query=<关键词>&order=time`（按时间排序）
- snapshot → 解析结果列表

**力扣**
- `browser` navigate → `https://leetcode.cn/discuss/?currentPage=1&orderBy=newest_to_oldest&query=<关键词>`（按最新排序）
- snapshot → 解析讨论帖列表

**V2EX**
- `browser` navigate → `https://www.v2ex.com/go/jobs`
- snapshot → 解析招聘帖列表

**掘金**
- `browser` navigate → `https://juejin.cn/search?query=<关键词>&type=0`
- snapshot → 解析搜索结果

**LinuxDO**（未登录，只看公开帖）
- `browser` navigate → `https://linux.do/search?q=<关键词>`
- 可能需要通过 Cloudflare 验证
- snapshot → 解析搜索结果

### 🔍📄 自由搜索补充（web_search + web_fetch，必要时 browser）

1. `web_search`：`<关键词> 校招 2026` 或 `<公司名> 内推`（优先搜近一周的结果）
2. 对搜索结果中的链接：
   - 先用 `web_fetch` 尝试读取页面内容
   - 如果 `web_fetch` 返回空内容或报错 → 改用 `browser` navigate + snapshot
3. 提取岗位信息
4. 或许前面几个渠道对央企国企收录信息不够需要特地补充

## 配置文件

- **求职偏好**：`{baseDir}/references/job-profile.md`
- **简历**：`{baseDir}/references/resume.md`（含在线简历 URL 或简历全文）
- **爬取缓存**：`{baseDir}/data/crawl_cache.db`（自动创建）
- **飞书多维表格**：
  - app_token: `YOUR_APP_TOKEN`
  - table_id: `YOUR_TABLE_ID`
  - **若表格不存在或为空，按以下 schema 创建字段**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 岗位名称 | 文本 | 职位标题 |
| 公司名称 | 文本 | 公司/组织名 |
| 薪资范围 | 文本 | 如 "20K-35K" |
| 工作城市 | 文本 | 如 "上海" |
| 来源渠道 | 单选 | BOSS/小红书/微信/牛客/力扣/LinuxDO/V2EX/掘金/自由搜索 |
| 来源URL | 链接 | 原始帖子/岗位页面链接 |
| 岗位描述 | 文本 | JD 关键信息摘要（不超过 500 字） |
| 匹配度 | 数字 | 0-100 AI 打分 |
| 发现日期 | 日期 | 首次采集的日期 |
| 状态 | 单选 | 待查看/已查看/已投递/不感兴趣 |
| 备注 | 文本 | AI 推荐理由或补充信息 |

## 每日执行流程

### 第1步：读取偏好
读取 `{baseDir}/references/job-profile.md` 获取偏好，读取 `{baseDir}/references/resume.md` 获取简历信息，综合生成搜索关键词组合：
关键词 × {校招, 秋招, 春招, 提前批, 应届生, 实习, 社招, 内推}

### 第2步：各渠道列表扫描
按上方"各渠道采集策略"执行。**优先扫描当日/近一周新发布的内容**，若当日新增不足再适当回溯更早的数据。收集岗位 URL 和基本信息。

### 第3步：爬取缓存过滤（第一层去重）
```bash
python {baseDir}/scripts/cache_manager.py check /tmp/urls.json
```

### 第4步：详情抓取（只对新 URL）
- 社媒/社区：browser navigate + snapshot
- 自由搜索结果：web_fetch 优先，失败则 browser

### 第5步：推荐历史过滤（第二层去重）
`feishu_bitable_list_records` 读取已有记录

### 第6步：AI 匹配打分（第三层过滤）
匹配度 0-100（低于 40 不推送）

### 第7步：写入飞书多维表格
`feishu_bitable_create_record`

### 第8步：发送每日摘要
通过飞书消息推送 Top 3

## 注意事项

- **BOSS直聘**：只用 web_search，绝对不要用 browser 打开任何 zhipin.com 页面
- **Clash 代理**：如使用 Clash TUN 模式，需配置 ssrfPolicy（见 README）
- **browser 使用**：每次只激活一个标签页，加随机延迟 2-5 秒，避免被反爬检测
- Cookie 过期后需要用户手动重新登录浏览器，有问题就先停下主动给用户发送（飞书）消息。
- LinuxDO 受 Cloudflare 防护，首次可能需手动通过验证
