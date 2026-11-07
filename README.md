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

### car-bar-mv-kit — 汽车酒吧 MV 素材流水线

输入**一张实拍汽车图片**，产出成套 MV 素材：2 张同场景男女双主唱舞台模板图，再各生成一段 5 秒动态片段。

定位不是「随便生成几张好看的图」，而是把一条**实测可复现的锚点链**固化下来，避开已验证失败的路线。

**核心能力**

| 环节 | 说明 |
|---|---|
| 场景立锚 | 单图生成现代东方夜店舞台，主唱与车后四人乐队均为中国面孔，展台车留作可替换位 |
| 双图融合 | 以实拍车作车型参考，AI 原生重绘到展台，自动匹配暖金舞台光、接触阴影与地面倒影 |
| 锚点派生 | 只传融合后的女歌手版单图派生男歌手版，锁死车辆形态、场景、乐队与灯光 |
| 去角标 | 本地画面修补抹除服务侧右下角角标，纯 Pillow 实现，保留完整画幅 |
| 图生视频 | 各 5 秒：主唱演唱口型与律动、乐队演奏、车原地不动仅光影流动、单一克制缓推 |
| 交付验收 | 抽帧核对主唱/车辆/乐队，读取真实时长与画幅，识别服务侧附带音轨 |

**产出**：2 张 2048×1152 PNG、2 条 2560×1440 / 24fps / 约 5 秒 MP4、一张成套画布与验收报告。

**关键原则**：禁止抠图合成（会出现硬边界与贴片感）、禁止并行独立生成两张图、禁止提交 `1080p`（接口仅 `768P` / `2K`）、不要试图用提示词关掉服务侧音轨（实测无效）；两条独立片段的车辆存在可见漂移，剪辑时用叠化或景别切换，不要硬接。

→ 详见 [`skills/car-bar-mv-kit/SKILL.md`](skills/car-bar-mv-kit/SKILL.md)

---

## 目录结构

```
skills/
├── company-research-report/
│   ├── SKILL.md              # 技能主文件：8 步工作流
│   ├── scripts/              # 可执行脚本
│   │   ├── recon.py             # 全站侦察 + 隐藏接口挖掘
│   │   ├── html_to_text.py      # 正文提取（跨页页眉页脚去重）
│   │   ├── fix_inner_quotes.py  # 修复中文文案里的 ASCII 双引号
│   │   └── verify_html.py       # 交付前三步校验
│   ├── references/           # 按需加载的参考文档
│   │   ├── research-playbook.md   # 调研渠道优先级、5 个踩过的坑、自查清单
│   │   ├── report-structure.md    # 12 章每章要求与硬性规范
│   │   └── interview-guide.md     # 提问模板、话术写法、三类关键人识别
│   ├── assets/               # 交互式报告模板
│   └── examples/             # 成品范例（含客户数据，不随公开仓库分发）
└── car-bar-mv-kit/
    ├── SKILL.md              # 技能主文件：默认规格 + Step 0~7 工作流
    ├── references/           # 提示词原文 / 硬约束 / 验收清单
    │   ├── prompts.md           # P1 场景锚点、P2 双图融合、P3 男歌手派生、P4 视频
    │   ├── constraints.md       # 12 项实测约束与失败路线
    │   └── acceptance.md        # 逐件与成套验收清单
    └── scripts/
        ├── remove_corner_badge.py  # 服务侧角标画面修补
        └── verify_video.py         # 成片规格 / 音轨 / 抽帧验收
```

---

## 开发约定

- 技能目录名即技能名，必须含 `SKILL.md` 且带 frontmatter（`name` / `description`）
- 脚本放 `scripts/`，按需加载的长文档放 `references/`，模板/静态资源放 `assets/`
- 交付前用 `skill-creator` 的 `quick_validate.py` 校验结构
- 面向 WorkBuddy 开放平台 / SkillHub 的技能另补 `slug` / `version` / `displayName` / `display_name*` 等扩展字段；`quick_validate.py` 会提示 `Unexpected key(s)`，属已知告警（现有技能同样如此），不影响安装与触发
- 涉及客户数据的产物不提交到公开仓库
