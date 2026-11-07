# 提示词模板（均为实测成功版本）

本文件收录已产出合格成片的提示词原文。占位符用 `{...}` 标记，替换时**只替换占位符，不要改写其余措辞**——这些措辞（尤其 INVARIANTS 与 EXCLUSIONS）是逐轮验证后固化下来的。

---

## 0. 车型特征卡（Step 0 产出）

读完输入车图后填这张卡，内容将作为 `{CAR_TRAITS}` 注入 P2 / P3 / P4。

```
车型类别与车身颜色：{如：白色紧凑型 SUV / 黑色轿车 / 银色 MPV}
拍摄角度与车头朝向：{如：左前 45°，车头朝画面右}
前脸：{格栅形状、大灯造型、下护板、前保险杠}
车侧：{黑色轮眉与侧裙包围、车顶行李架、腰线、后视镜}
轮毂：{颜色与辐条样式}
标识：{车标位置、牌照板是否有中文小字}
光照条件：{白天户外平光 / 棚拍 / 夜景}
原图像素：{宽×高}
```

写成英文短句填入 P2，例如：
`a white compact SUV, boxy upright silhouette, left-front three-quarter angle with the front pointing RIGHT of frame, black trapezoid lower grille, slim angular headlights, pronounced black wheel-arch cladding and black lower body side skirts, silver roof rails, silver multi-spoke alloy wheels, Toyota emblem on the front, and a white license plate frame with subtle small lettering`

**保留车标/牌照文字的口径**：若用户选择去掉，把 `Toyota emblem`、`license plate frame with lettering` 改成 `no emblem, blank plate`；若选择保留，必须提前说明中文小字不可精确还原。

---

## 1. 共享片段（拼装用，逐字复用）

### `{CHINESE_FACE_FEMALE}`
`Authentic Chinese facial features: natural East Asian bone structure, straight black hair, dark brown eyes, natural Chinese skin tone, realistic Chinese face shape. NOT Eurasian, NOT mixed-race, NOT Westernized features, NOT Caucasian bone structure.`

### `{CHINESE_FACE_MALE}`
`authentic natural Chinese facial features: East Asian bone structure, short black hair, dark brown eyes, natural Chinese skin tone; NOT Eurasian, NOT mixed-race, NOT Westernized, NOT Caucasian bone structure.`

### `{SCENE_INVARIANTS}`
`the contemporary Oriental nightclub interior (deep ink-green lacquer walls, restrained vermilion accents, warm gold lighting, Chinese geometric lattice patterns, glowing circular moon-gate halo behind the stage, dark polished stone floor), volumetric spotlights, atmospheric haze, shallow depth of field, film grain and the overall cinematic color grade`

### `{EXCLUSIONS}`
`no text, no Chinese characters, no calligraphy, no lettering, no signage, no added logos, no brand names, no watermarks, no UI overlays, no annotations, no extra cars, no extra people, no props in front of the car`

### `{LIGHT_BLOCK}`
`warm gold overhead stage spotlights with restrained vermilion-red rim accents against deep ink-green shadows, volumetric light beams drifting slowly through atmospheric haze, subtle film grain, cinematic music-video grade, intimate live-performance energy`

---

## 2. P1 · 场景锚点（Step 1，文生图）

参数：`size=2048x1152`、`quality=hd`。用途：给 Step 2 提供干净构图，**不交付**。

```
Photorealistic cinematic wide shot, 16:9 horizontal, 2K, premium music-video key visual in a CONTEMPORARY ORIENTAL NIGHTCLUB style.

SETTING: {STYLE_BLOCK}

THREE DEPTH PLANES, carefully layered:
1) FOREGROUND, lower-left third — a young Chinese female lead singer, standing, singing passionately into a handheld microphone, eyes closed, one hand reaching outward, elegant black stage outfit with subtle dark-red detailing. {CHINESE_FACE_FEMALE} Warm gold key light modeling her face, gentle lens flare. She is the emotional focal point.
2) MID-GROUND, on an elevated circular display platform ABOVE and behind the stage, centered — ONE complete unbranded neutral concept car in a clean front three-quarter view, all four wheels fully visible, single solid matte silver-grey body, absolutely no logo, no grille emblem, no license plate, no lettering, no decals, no model-specific signature details. The car sits isolated on a simple dark round pedestal with generous clean empty space all around its entire silhouette, evenly lit with a crisp soft rim light so the outline is sharp and easy to replace in post-production. NOTHING overlaps or occludes the car: no people, no instruments, no cables, no props, no decorative screens in front of it.
3) BACKGROUND, on a deeper raised tier behind the car — a four-piece live band (drummer, electric guitarist, bassist, keyboardist) actively playing, slightly out of focus, silhouetted against the warm moon-gate backlight. All four musicians are Chinese with authentic natural Chinese facial features and black hair, no Western or mixed-race faces.

LIGHTING & GRADE: overhead warm gold stage spotlights, restrained vermilion rim accents against deep ink-green shadows, volumetric light beams through atmospheric smoke, shallow depth of field, subtle film grain, high dynamic range, elegant dark premium cinematic mood.

STRICT EXCLUSIONS: {EXCLUSIONS}, no license plates. A clean plate engineered for post-production car replacement.
```

### `{STYLE_BLOCK}` 默认值（现代东方夜店）

```
An upscale automotive-themed live music bar in modern Chinese style, at night. Deep ink-green (dark teal-green) lacquered walls, restrained vermilion-red accents, warm gold ambient lighting. Traditional Chinese geometric lattice window patterns on walls and ceiling, a large softly glowing circular "moon gate" light halo behind the stage, dark carved wood screens, polished dark stone floor with soft reflections, light atmospheric haze. The Chinese character lives ONLY in the architecture, color palette and light shapes — it must never compete with the car. Do NOT include Western industrial steel beams, leather booths, neon signs or bottle shelves.
```

备选（用户改风格时替换；改风格＝作废旧锚点、重立新锚点，不沿用上一套参考图）：
- **赛博霓虹夜场**：蓝紫粉霓虹、镜面与光带，车改冷银/珍珠白融入冷调。
- **复古港风胶片**：80 年代夜总会暖红暖黄、丝绒幕与串灯、胶片颗粒。
- **高对比黑白舞台**：只留黑白与一束顶光，极简戏剧性，车为哑光深灰（酒吧感最弱）。
- **电影感工业酒吧**（最早版本）：深炭灰、暖琥珀钨丝光 + 冷青蓝霓虹、工业钢梁、皮质卡座、酒瓶架柔光。

---

## 3. P2 · 双图融合（Step 2，图生图，核心）

参数：`images=[场景锚点图, 输入车图]`（顺序不可颠倒）、`size=2048x1152`。
这是整套流程质量最关键的一步：**必须原生重绘，不是拼贴**。

```
You are given TWO images: IMAGE A is the main scene to edit (a cinematic 16:9 music-video stage key visual). IMAGE B is a real photo of {CAR_SHORT}, used ONLY as a vehicle shape reference.

TASK: Replace the matte silver-grey unbranded concept car sitting on the elevated circular display platform in IMAGE A with the exact {CAR_SHORT} from IMAGE B. Do this by RE-RENDERING / RE-PAINTING the vehicle natively into the scene so it is fully lit by the stage lighting — absolutely NOT a cut-and-paste collage, no white outline, no photographic daylight flat lighting, no asphalt parking-lot ground, no original photo background, no rectangular patch, no seam, no ghost edge.

THE VEHICLE (from IMAGE B): {CAR_TRAITS}. Keep believable real-car proportions, all four wheels visible, sharp clean silhouette.

INTEGRATION RULES: The car must sit naturally ON the same circular dark display pedestal at the same position and scale as the old car, with correct perspective. Give it warm gold key light from the overhead stage spotlights, restrained vermilion-red rim accents, deep ink-green shadows, a soft contact shadow where the tires meet the pedestal, and a subtle warm reflection on the polished dark stone floor. Its paint must be graded into the warm nightclub color temperature (not pure daylight white). It must read as a real car physically present in this nightclub, with gentle atmospheric haze in front of it. Remove EVERY trace of the old silver-grey concept car — no leftover roofline, fastback curve, wheels, or body panels.

INVARIANTS — DO NOT CHANGE ANY OF THE FOLLOWING: the exact 16:9 horizontal framing and 2048x1152 aspect; {SCENE_INVARIANTS}; the young Chinese female lead singer in the foreground lower-left third, her face, black stage outfit, handheld microphone, pose and warm key light; the four Chinese band members on the deeper raised tier behind the car, their number, positions and instruments; atmospheric smoke, volumetric light beams, shallow depth of field, film grain, and the overall cinematic color grade.

STRICT EXCLUSIONS: {EXCLUSIONS}. The bottom-right corner must remain pure dark background with no corner badge.
```

`{CAR_SHORT}` 为车型简称，如 `a WHITE TOYOTA RAV4 SUV`。

---

## 4. P3 · 男歌手派生（Step 3，图生图）

参数：`images=[Step 2 成品图]`（**只传一张**）、`size=2048x1152`。

```
Use the reference image as the STRICT visual anchor for a companion key visual in the same series. Keep everything identical except ONE change.

CHANGE ONLY ONE THING: replace the young Chinese female lead singer in the foreground lower-left third with a young handsome CHINESE male lead singer in the same position and the same singing pose — standing, holding a handheld microphone close to his mouth, singing passionately with eyes closed, one arm reaching outward with an open hand, wearing the same black stage outfit with subtle dark-red detailing and a waist belt, with the same warm gold key light direction on his face. He must have {CHINESE_FACE_MALE}

ABSOLUTE INVARIANTS — the {CAR_SHORT} on the circular pedestal must be reproduced EXACTLY as in the reference image: {CAR_TRAITS}, and identical position, scale, proportions, perspective, warm gold stage lighting, soft contact shadow and floor reflection. Do NOT redraw, restyle, recolor, resize, rotate or move the car, and do NOT change it back into a generic concept car. Also keep unchanged: the exact 16:9 framing; {SCENE_INVARIANTS}; the four Chinese band members on the raised tier, their number, positions and instruments; the overall color grade.

STRICT EXCLUSIONS: {EXCLUSIONS}. The bottom-right corner must remain pure dark background — do NOT reproduce any small corner badge or watermark from the reference image.
```

---

## 5. P4 · 5 秒动态视频（Step 5，图生视频）

参数：`first_frame=对应成品图`、`duration=5`、`resolution=2K`、`aspect_ratio=16:9`。
两段提示词**逐字复用，仅替换 `{VOCAL}` / `{PRONOUN}` 组**，否则会加大跨片段漂移。

```
Cinematic 5-second live-performance shot, 16:9 horizontal. Use the provided image as the exact first frame: a contemporary Oriental nightclub stage with {VOCAL} in the foreground lower-left, {CAR_SHORT} standing on a circular display pedestal in the center, and a four-piece Chinese band on the raised tier behind.

SUBJECT MOTION: {VOCAL} is actively singing into {PRONOUN_POSS} handheld microphone — natural lip movements opening and closing in a singing rhythm, subtle head sway, gentle shoulder and torso movement, {PRONOUN_POSS} free hand gesturing expressively, {HAIR} moving slightly, mostly closed eyes with an occasional natural blink. Keep {PRONOUN_POSS} face, hairstyle, black stage outfit and identity exactly as in the first frame. On the raised tier behind the car, the four Chinese band members play their instruments with small continuous motions: the drummer's sticks striking, the guitarist and bassist strumming and fretting, the keyboardist's hands moving on the keys, slight body sway. All musicians keep their faces, outfits, instruments and positions unchanged.

THE CAR — CRITICAL INVARIANT: {CAR_SHORT} stays completely stationary on the circular pedestal. No driving, no rotation, no wheel turning, no change of position, no change of shape, proportions, viewing angle, grille, wheel-arch cladding, roof rails, wheels, emblem or license plate. Only light moves across it: a slow warm gold spotlight sweep gliding over the body panels, soft specular highlights travelling along the hood and shoulder line, headlights glowing subtly brighter, and the floor reflection shimmering gently in sync with the moving light.

CAMERA: one single restrained slow push-in toward the stage, very slight. No pan, no tilt, no orbit, no zoom burst, no cut, no camera shake.

LIGHT & ATMOSPHERE: {LIGHT_BLOCK}. The glowing circular moon-gate halo and Chinese geometric lattice patterns stay in place.

END STATE: the shot settles back on the same three-plane composition — singer in the foreground, unchanged car centered on its pedestal, band behind — with the warm spotlight resting on the car. No fade to black, no scene change, no ending card.

STRICT EXCLUSIONS: {EXCLUSIONS}, no subtitles, no lyrics overlay, no morphing or distortion of faces, hands, instruments or the car body.
```

| 占位符 | 女歌手版 | 男歌手版 |
|---|---|---|
| `{VOCAL}` | `a young Chinese female lead singer` | `a young handsome Chinese male lead singer` |
| `{PRONOUN_POSS}` | `her` | `his` |
| `{HAIR}` | `hair` | `short black hair` |

**不要**在 P4 里写「静音 / 无音轨」要求——已实证无效，服务侧仍会附加音轨，写了只会污染提示词。音轨统一在交付说明里提示后期处理。

---

## 6. 提交参数速查

| 步骤 | 能力 | 关键参数 |
|---|---|---|
| P1 | 文生图 | `size=2048x1152`, `quality=hd` |
| P2 | 图生图（2 图） | `images=[锚点, 车图]`, `size=2048x1152` |
| P3 | 图生图（1 图） | `images=[女歌手成品]`, `size=2048x1152` |
| P4 | 图生视频 | `first_frame`, `duration=5`, `resolution=2K`, `aspect_ratio=16:9` |
