# workbuddy-skills

WorkBuddy 自研 Agent 技能集合。每个技能一个目录，可直接安装到 `~/.workbuddy/skills/` 使用。

## 安装

```bash
git clone https://github.com/itfamer666/workbuddy-skills.git
cp -R workbuddy-skills/skills/<技能名> ~/.workbuddy/skills/
```

装好后直接对话触发，或在 WorkBuddy 里用 `/<技能名>` 调用。

---

## 技能清单

### company-research-report — 企业研究报告生成器

输入一个企业网址或名称，产出一份**能和董事长对话的交互式研究报告**。

定位不是行业分析，而是**成交前的认知底稿**：每一章都要回答"这能帮我更好地谈下这单吗"。

**核心能力**

| 环节 | 说明 |
|---|---|
| 全站侦察 | curl 抓取原始 HTML（绕开 JS 渲染），自动发现子页、下载业务 JS |
| 隐藏接口挖掘 | 从 JS 里正则挖接口并逐个探测，**对返回空的自动补参重试**（POST / 带分页参数） |
| 外部情报 | 管理层姓名职务、本年度战略关键词（年会发言原话）、营收排名、IT 供应商 |
| 交叉核对 | 同一指标在不同来源的差异表（客户数/门店数/营收经常对不上） |
| 交互报告 | 单文件 HTML：侧栏导航、KPI 动画、品牌分布图点击联动、园区搜索筛选、AI 机会分级、提问清单 |
| 交付前校验 | 语法 → 运行时 → 渲染条数三步断言，避免单文件 HTML 白屏 |

**产出**：12 章交互式研究报告，含管理层地图、AI 机会地图（P0~P3）、破冰提问清单。

**关键原则**：接口数据 > 网页文案 > 第三方报道；每个 AI 场景必须能溯源到对方公开说过的话，
且要有对口人 + 可量化指标；永远避开"风口/颠覆/替代人/裁员"叙事。

→ 详见 [`skills/company-research-report/SKILL.md`](skills/company-research-report/SKILL.md)

---

## 目录结构

```
skills/
└── company-research-report/
    ├── SKILL.md              # 技能主文件：8 步工作流
    ├── scripts/              # 可执行脚本
    │   ├── recon.py             # 全站侦察 + 隐藏接口挖掘
    │   ├── html_to_text.py      # 正文提取（跨页页眉页脚去重）
    │   ├── fix_inner_quotes.py  # 修复中文文案里的 ASCII 双引号
    │   └── verify_html.py       # 交付前三步校验
    ├── references/           # 按需加载的参考文档
    │   ├── research-playbook.md   # 调研渠道优先级、5 个踩过的坑、自查清单
    │   ├── report-structure.md    # 12 章每章要求与硬性规范
    │   └── interview-guide.md     # 提问模板、话术写法、三类关键人识别
    ├── assets/               # 交互式报告模板
    └── examples/             # 成品范例（含客户数据，不随公开仓库分发）
```

---

## 开发约定

- 技能目录名即技能名，必须含 `SKILL.md` 且带 frontmatter（`name` / `description`）
- 脚本放 `scripts/`，按需加载的长文档放 `references/`，模板/静态资源放 `assets/`
- 交付前用 `skill-creator` 的 `quick_validate.py` 校验结构
- 涉及客户数据的产物不提交到公开仓库
