---
name: company-research-report
slug: company-research-report
version: 1.0.1
displayName: 企业研究报告生成器
display_name: 企业研究报告生成器
display_name_en: Company Research Report Generator
summary: 输入一个网址或企业名，产出能和董事长对话的交互式研究报告——全站侦察、隐藏接口挖掘、管理层地图、AI 机会地图一气呵成。
description: '输入一个企业网址或企业名称，产出可用于 AI 应用落地前期沟通的「交互式企业研究报告」。自动做全站侦察（含隐藏数据接口挖掘）、外部情报交叉验证、12 章报告撰写、单文件交互 HTML 输出与交付前校验。当用户说“调研这家公司”“看看这个网站”“出一份 XX 的研究报告”“了解下 XX 企业”“做客户背景调查”“见面前的背景材料”时使用。'
description_zh: '输入一个企业网址或企业名称，产出可用于 AI 应用落地前期沟通的「交互式企业研究报告」。自动做全站侦察（含隐藏数据接口挖掘）、外部情报交叉验证、12 章报告撰写、单文件交互 HTML 输出与交付前校验。当用户说“调研这家公司”“看看这个网站”“出一份 XX 的研究报告”“了解下 XX 企业”“做客户背景调查”“见面前的背景材料”时使用。'
description_en: 'Enter a company website or company name to produce an interactive enterprise research report for pre-sales AI adoption conversations. Performs full-site reconnaissance (including hidden data API discovery), cross-validates external intelligence, writes a 12-chapter report, and emits a single-file interactive HTML with pre-delivery validation. Use when the user asks to research a company, review a website, produce a research report on a target, understand an enterprise, run customer background checks, or prepare pre-meeting briefing materials.'
tags: [调研, 企业研究, 报告生成, AI落地, 客户背景, 竞调]
license: MIT
agent_created: true
---

# 企业研究报告生成器

把一个网址或企业名，变成一份**能和董事长对话的交互式研究报告**。

报告的定位不是行业分析，而是：**成交前的认知底稿**。
每一章都要回答"这能帮我更好地谈下这单吗"，答不上来的章节不写。

---

## 何时使用

- 用户给了一个网址或企业名，要求"调研 / 研究 / 了解 / 出报告"
- 需要为某次客户拜访、提案、AI 落地立项准备背景材料
- 需要摸清目标企业的基本面、管理层、数字化现状、战略诉求

---

## 工作流程

### 第 1 步 · 全站侦察

```bash
mkdir -p ./<企业名>调研 && cd <企业名>调研
python3 ~/.workbuddy/skills/company-research-report/scripts/recon.py <网址> -o .
```

用户只给了企业名时，先用 WebSearch 找官网再跑。

跑完**先读 `recon-report.md`**：它会告诉你是不是 JS 渲染页、哪些隐藏接口命中了 JSON、各多少条。

脚本会自动完成：发现站内链接 → 抓子页 → 下载站内 JS → 从 JS 里正则挖接口 → 逐个探测
→ **对返回空的接口再补参重试**（POST JSON / POST 表单 / GET 带 `pageNum&pageSize`）。
新闻、留言、名单这类接口默认 GET 常返回空，补参后往往能救回来，小结里会注明调用方式。

过程中还会自动避坑：跳过前端模板占位符链接（`${...}`）、按内容哈希跳过重复分页、
跳过 jquery/vue/echarts 等公共库 JS（只下业务 JS）、丢弃 `/https://xxx` 这类畸形链接。
**抓取配额只计入"成功抓到的唯一页"**，不会被 `?page=0/1/2` 吃光。

> ⚠️ **不要用 WebFetch 直接读目标站点。** 现代官网多为 JS 渲染，WebFetch 常只拿到
> `API接口单元` 之类的占位符。侦察脚本已用 curl + 浏览器 UA 抓好了原始 HTML。

> 站点间歇性 502 很常见。脚本已内置 3 次重试；若首页仍打不开会明确报错并给出退路
> （换 https / 去 www / 改用 WebSearch 调研，并在报告第 12 章注明"官网不可访问"）。
> **隔 20 分钟再试往往就好了**，不要因为一次失败就放弃接口挖掘。

### 第 2 步 · 读页面正文

```bash
python3 scripts/html_to_text.py ./raw -o pages.txt --dedupe
```

`--dedupe` 剔除各页重复的导航页脚。正文很长时用 `--max-chars` 分段或 `--per-file` 逐页读。

### 第 3 步 · 读接口数据

`Read` 直接看 `api/*.json`。**接口数据准确度高于网页文案**，定量章节以它为准。

### 第 4 步 · 外部情报补充（WebSearch）

详见 `references/research-playbook.md` 的 Step 4。重点是这几类：

| 搜索主题 | 拿什么 |
|---|---|
| `<公司> 董事长 总经理 总裁` | 管理层姓名职务、家族/职业经理人结构 |
| **`<公司> <今年> 年会 / 半年会 / 工作会`** | ⭐ **最高价值**：管理层发言原话、当年战略关键词 |
| `<公司> 营收 百强 排名` | 体量与行业地位 |
| `<公司> OA / CRM / 数字化` | IT 供应商反推（搜供应商官网的客户案例页） |
| `<公司> 工商信息` | 法人、注册资本、成立日期 |

第二行的年会搜索**必须做** —— 搜到的管理层原话是后续 AI 方案立项的最佳依据。

### 第 5 步 · 交叉核对

把同一指标在不同来源的值列成差异表（客户数、门店数、营收、员工数经常对不上）。
这份表就是报告第 12 章，也能当开场话题。

### 第 6 步 · 生成交互报告

```bash
cp ~/.workbuddy/skills/company-research-report/assets/interactive-report-template.html \
   <企业名>研究报告_交互版.html
```

**动手前先翻一眼 `examples/` 里的成品报告**（若有）—— 看清楚"什么叫做写透了"再动笔，
能显著提升信息密度。目录为空时，至少照着 `assets/` 模板里每个字段的注释要求写满。

编辑模板中 `★★★ DATA BLOCK —— 只需替换这一段 ★★★` 之间的内容：

| 变量 | 填什么 |
|---|---|
| `CFG` | 公司名、一句话画像、hero 标签、日期、各章节标题文案 |
| `KPIS` | 4~8 个核心指标，**每项都要标来源** |
| `TIMELINE` | 发展历程，`k:1` 标记转折年 |
| `PEOPLE` | 三层管理层：决策层 / 经营层 / 业务对口；每人含 `f`（关心什么）+ `d`（沟通要点 HTML） |
| `BIZ` | 业务板块 Tab，`h` 用反引号包裹的 HTML |
| `ITEMS` | 可搜索的明细清单（园区/门店/子公司/产品线），没有就 `[]` |
| `CAT_MAP` | 标签 → 分类 + 配色，驱动第 5 章分布图 |
| `AI` | AI 机会 P0~P3，每项必须写清：场景、痛点、**对应其哪个战略关键词**、对口人、可量化指标 |
| `QUESTIONS` | 破冰提问清单，模板见 `references/interview-guide.md` |
| `STATIC` | 6 段静态 HTML：速览、文化、数字化诊断、战略重心、沟通策略、风险 |

某组数据没有就留 `[]`，对应章节自动隐藏、导航自动重编号。**宁肯留空不要编。**

写作规范详见 `references/report-structure.md`。

### 第 7 步 · 交付前校验（必做）

```bash
# 1. 修复中文文案里的 ASCII 双引号 —— 不修会直接白屏
python3 scripts/fix_inner_quotes.py <企业名>研究报告_交互版.html

# 2. 三步校验：语法 → 运行时 → 渲染条数
python3 scripts/verify_html.py <企业名>研究报告_交互版.html \
  --expect '#kpis|kpi|4' --expect '#itemList|pitem|39' --expect '#sec10|aic|13'
```

断言格式：`容器选择器|条目class名|期望数量`，可传多次。
全部 ✅ 才可交付。单文件交互页一旦有语法错误就是整页白屏，**不要跳过这一步**。

### 第 8 步 · 交付

用 `present_files` 打开交互版。若用户需要可打印 / 可作附件的版本，再另存一份静态版。

---

## 关键原则

1. **接口数据 > 网页文案 > 第三方报道**，对外只用官网口径
2. **每个 AI 场景要能溯源到对方公开说过的话**，溯不到源的删掉
3. **每个 AI 场景要有对口人 + 可量化指标**，两者缺一的不留
4. **永远避开"风口 / 颠覆 / 替代人 / 裁员"叙事** —— 对方愿景若含"最佳雇主"更要小心
5. **识别出唯一的否决点**（通常是 IT / 风控负责人），并在报告里标注"必须提前单独沟通"
6. **提案打样板间**：1 个业务单元 + 1 个场景，4~6 周出效果，再借对方已有动员机制复制

---

## 参考资源

| 文件 | 何时读 |
|---|---|
| `references/research-playbook.md` | 调研开始前 —— 渠道优先级、搜索清单、5 个踩坑、产出前自查表 |
| `references/report-structure.md` | 写报告时 —— 12 章每章要求与硬性规范 |
| `references/interview-guide.md` | 写第 3、11 章时 —— 提问模板、话术写法、三类关键人识别 |
| `assets/interactive-report-template.html` | 第 6 步直接复制使用 |
| `examples/` | ⭐ **填数据前先看成品** —— 存放以往交付过的完整报告，照着它的信息密度写。目录可能为空（范例含客户数据，不随公开仓库分发） |
| `scripts/recon.py` | 第 1 步全站侦察 |
| `scripts/html_to_text.py` | 第 2 步正文提取 |
| `scripts/fix_inner_quotes.py` | 第 7 步引号修复 |
| `scripts/verify_html.py` | 第 7 步交付前校验 |
