---
name: ark-media
description: >
  图像与视频生成技能（多渠道）。当前已接入火山方舟 (Volcengine Ark) 的 Seedream 图像生成和
  Seedance 视频生成模型。支持文生图、图生图、文生视频、图生视频、多模态参考、视频编辑/延长、
  虚拟人像、有声视频等。当用户提到生图、生视频、seedance、seedream、火山方舟、视频编辑时触发。
---

# ark-media — 图像与视频生成

多渠道图像与视频生成技能。当前已接入火山方舟。

## 边界

`ark-media` 只负责接收已经准备好的内容输入，然后调用模型生图、生视频。

它不负责：
- 剧情规划
- 分镜拆解
- 角色/场景/道具 canon 管理
- continuity 判断
- 项目目录脚手架
- 上层创作决策

这些都应该由上层 skill 处理，例如 FilmForge。`ark-media` 是执行层，不是导演层。

## 快速路由

| 用户意图 | 去哪 |
|---------|------|
| 生成图片、修图、生组图 | [image/](references/image/) |
| 生成视频、编辑视频、延长视频 | [video/](references/video/) |

## 已接入渠道

### 火山方舟 (Volcengine Ark)

- **Base URL:** `https://ark.cn-beijing.volces.com/api/v3`
- **认证:** `ARK_API_KEY` 环境变量
- **API Key 管理:** https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
- **SDK:** `pip install 'volcengine-python-sdk[ark]'`

## 参考文档索引

### 图像生成 (`references/image/`)

| 文件 | 内容 |
|------|------|
| [models.md](references/image/models.md) | Seedream 5.0/4.5/4.0/3.0 模型矩阵、像素值、限流 |
| [api-reference.md](references/image/api-reference.md) | 图像 API 全参数、OpenAI 兼容、流式事件 |
| [generation.md](references/image/generation.md) | 文生图、图生图、多图融合、组图、联网搜索、流式 |
| [prompt-guide.md](references/image/prompt-guide.md) | 提示词公式、各场景技巧、风格关键词 |

### 视频生成 (`references/video/`)

| 文件 | 内容 |
|------|------|
| [models.md](references/video/models.md) | Seedance 全系列模型对比、像素值、限流 |
| [api-reference.md](references/video/api-reference.md) | 视频 API 全参数、任务管理、离线推理、Webhook |
| [generation.md](references/video/generation.md) | 文生视频、首帧/首尾帧/参考图、连续视频、样片模式 |
| [prompt-guide.md](references/video/prompt-guide.md) | 提示词公式、文字生成、图片/视频参考、编辑技巧 |
| [multimodal-input.md](references/video/multimodal-input.md) | 多模态组合约束、素材指代规则 |
| [editing.md](references/video/editing.md) | 编辑、延长、轨道补齐 |
| [portrait-and-creation.md](references/video/portrait-and-creation.md) | 虚拟人像、已授权真人素材、模型产物二创 |

### 通用 (`references/shared/`)

| 文件 | 内容 |
|------|------|
| [limitations.md](references/shared/limitations.md) | 输入规格、图片裁剪、数据保存、合规要求 |
| [pricing.md](references/shared/pricing.md) | 图像按张、视频按 token 定价、费用速算公式 |

## Agent 行为规范

- 提交前确认对应渠道的 API Key 已设置
- 视频是异步的：提交 → task_id → 轮询
- 消耗积分/余额前先警告用户
- 视频产物 URL **24h 过期**，重要结果提醒用户及时保存
- 小批量、可审查地出图/出视频，记录每次调用的参数、task_id、状态
- 写提示词前，先读对应的 prompt-guide 匹配合适的模板
- 用户追求速度时用 fast/lite 模型，除非明确要最高品质
- **输出路径**：图像默认保存到 `~/Downloads`（`--output-dir` 可覆盖），视频轮询完成后也自动下载到 `~/Downloads`。**禁止输出到 workspace 目录**
- **每次生成结束后必须向用户报告**：使用模型、费用、输出文件路径
- **即梦/Seedance 提示词使用中文**，模型对中文理解更好；Seedream 图像可用中英文
- 如果用户给的是“创意意图”而不是可执行内容输入，先提醒应由上层 skill 整理输入后再交给 `ark-media`
- **参数确认规则（强制）**：用户未明确指定时，**必须先确认再提交**，禁止默认猜测后直接出：
  - 图像：模型（默认 seedream-5.0）、尺寸、数量、风格倾向
  - 视频：分辨率（**默认 480p 预览**）、比例、时长（**默认 5s**）、是否有首帧参考图、有声/无声
  - **每次确认时必须附带预估费用**
  - 用户明确回复「确认」「出」「可以」等后才提交任务
  - 费用受比例影响（竖版像素量 > 横版），预估仅供参考，最终以 API 返回为准

- **分辨率升级策略（推荐）**：
  - **首次出视频强烈建议先出 480p 预览**（¥0.80/5s），确认效果满意后再用同一 `seed` 升级到 720p/1080p
  - API 返回的 `seed` 字段可用于复现：相同 seed + 相同提示词 + 相同首帧图 = 相同内容，仅清晰度不同
  - **注意：`generate_audio`（有声/无声）切换时，即使 seed 相同，画面可能有微调**（音频与画面联动生成）
  - 所以**稳妥的升级路径**：
    1. 先确认**有声还是无声**（一次性定死，后面不切换）
    2. 首次出 **480p** 预览（最低成本确认画面效果）
    3. 满意后用同一 `seed` 升级 **720p 或 1080p**（仅改分辨率，画面一致）
    4. 每步只改一个参数，避免跨变量跳跃

## CLI 工具

**脚本路径：** `skills/ark-media/scripts/ark_media.py`（位于本 skill 目录下，非 workspace 根目录的 `scripts/`）

```bash
# 费用估算（不需要 API Key）
python scripts/ark_media.py cost image --model seedream-5.0 --count 4
python scripts/ark_media.py cost video --model seedance-1.5 --resolution 480p --ratio 9:16 --duration 5

# 文生图（无参考图）
python scripts/ark_media.py generate-image "中文提示词" --model seedream-5.0 --size 2K

# 单图编辑（图生图：换风格/材质/背景）
python scripts/ark_media.py generate-image "保持姿势不变，将服装改为清水材质" \
  --model seedream-5.0 --image /path/to/input.jpg

# 多图融合（多张参考图 → 一张结果）
python scripts/ark_media.py generate-image "将图1的服装换到图2的人物上" \
  --model seedream-5.0 --images /path/to/img1.jpg /path/to/img2.jpg

# 组图生成（基于参考图出多张，最多4张）
python scripts/ark_media.py generate-image "参考这个LOGO做一套品牌视觉设计" \
  --model seedream-5.0 --image /path/to/logo.png \
  --sequential auto --max-images 4

# 多图生组图（多参考图 + 多输出）
python scripts/ark_media.py generate-image "生成3张女孩和奶牛玩偶在游乐园的图片" \
  --model seedream-5.0 --images /path/to/girl.png /path/to/cow.png \
  --sequential auto --max-images 3

# 创建视频任务（中文提示词 + 首帧参考图）
python scripts/ark_media.py generate-video "中文提示词" --model seedance-1.5 \
  --resolution 480p --ratio 9:16 --duration 5 --image /path/to/poster.png

# 多模态参考生视频（Seedance 2.0）
python scripts/ark_media.py generate-video "参考视频1的运镜，参考图片1的人物形象，参考音频1的背景音乐生成广告片" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 8 \
  --reference-images /path/to/lead.png \
  --reference-videos https://example.com/cam-ref.mp4 \
  --reference-audios https://example.com/bgm.mp3 \
  --input-duration 6

# 轨道补齐 / 多段串联（Seedance 2.0）
python scripts/ark_media.py generate-video "视频1中的拱形窗户打开，进入美术馆室内，接视频2，之后镜头进入画内，接视频3" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 8 \
  --reference-videos https://example.com/v1.mp4 https://example.com/v2.mp4 https://example.com/v3.mp4 \
  --input-duration 15

# 连续视频生成（返回尾帧，供下一个镜头接力）
python scripts/ark_media.py generate-video "中文提示词" --model seedance-2.0 \
  --resolution 480p --ratio 16:9 --duration 5 --image /path/to/poster.png \
  --return-last-frame

# dry run：只打印最终请求体，不实际提交
python scripts/ark_media.py generate-video "中文提示词" --model seedance-2.0 \
  --reference-videos https://example.com/v1.mp4 https://example.com/v2.mp4 \
  --input-duration 10 --dry-run

# 轮询视频结果（完成后自动下载到 ~/Downloads）
python scripts/ark_media.py poll <task_id>

# 查询任务列表
python scripts/ark_media.py list-tasks --status succeeded

# 取消任务
python scripts/ark_media.py cancel <task_id>
```

**注意：**
- 视频相关操作使用 REST API 直接调用（SDK 的 `contents` 接口不可用）
- **Seedance 视频提示词必须使用中文**，模型对中文理解显著优于英文
- Seedream 图像提示词中英文均可
- `--reference-videos` / `--reference-audios` 当前仅接受公网 URL 或 `asset://<id>`，不支持本地文件直传
- 若使用 `--reference-videos`，建议同时填写 `--input-duration`，否则费用估算会偏低
- `poll` 在检测到 `last_frame_url` 时会一并下载尾帧到 `~/Downloads`
- `--dry-run` 适合联调 packet / prompt / 多模态组合，先看 request body 再决定是否真的扣费提交

模型名支持简写：seedream-5.0 / seedance-2.0 / seedance-1.5 等。

依赖：`pip install 'volcengine-python-sdk[ark]'`

## 官方文档 URL（定期检查更新）

以下 URL 是所有参考文档的数据来源，建议每月至少检查一次，重点关注：定价变动、新增模型/分辨率、参数变更、限流调整。

### 核心 API 文档

| 文档 | URL | 关注点 |
|------|-----|--------|
| 视频生成 API 总览 | https://www.volcengine.com/docs/82379/1520758 | API 结构变更 |
| 创建视频生成任务 | https://www.volcengine.com/docs/82379/1520757 | 新参数、新模型 ID |
| 查询视频生成任务 | https://www.volcengine.com/docs/82379/1521309 | 返回字段变更 |
| 查询视频生成任务列表 | https://www.volcengine.com/docs/82379/1521675 | 筛选参数变更 |
| 取消/删除视频生成任务 | https://www.volcengine.com/docs/82379/1521720 | 接口变更 |
| 图像生成 API | https://www.volcengine.com/docs/82379/1541523 | 新参数、新模型 |
| 图像生成流式响应 | https://www.volcengine.com/docs/82379/1824137 | 流式事件格式 |

### 定价与限制

| 文档 | URL | 关注点 |
|------|-----|--------|
| 模型价格（总） | https://www.volcengine.com/docs/82379/1544106 | **定价变动、新模型价格** |
| 使用限制 | https://www.volcengine.com/docs/82379/1366799 | 限流调整、文件大小限制 |

### 教程与提示词指南

| 文档 | URL | 关注点 |
|------|-----|--------|
| Seedance 2.0 系列教程 | https://www.volcengine.com/docs/82379/2291680 | 新能力、分辨率变更 |
| Seedance 2.0 提示词指南 | https://www.volcengine.com/docs/82379/2222480 | 提示词技巧更新 |
| Seedance 1.5 pro 提示词指南 | https://www.volcengine.com/docs/82379/2168087 | 分辨率确认 |
| Seedance 1.0 pro/pro-fast 指南 | https://www.volcengine.com/docs/82379/1631633 | 1080p 确认 |
| Seedance 1.0 lite 提示词指南 | https://www.volcengine.com/docs/82379/1587797 | lite 分辨率 |
| Seedream 4.0-5.0 教程 | https://www.volcengine.com/docs/82379/1824121 | 新模型能力 |
| Seedream 3.0 教程 | https://www.volcengine.com/docs/82379/1824692 | 旧模型兼容 |
| Seedream 4.0-5.0 提示词指南 | https://www.volcengine.com/docs/82379/1829186 | 提示词技巧 |
| Seedream 3.0 提示词指南 | https://www.volcengine.com/docs/82379/1795150 | 旧模型提示词 |
| 视频生成通用教程 | https://www.volcengine.com/docs/82379/2298881 | SDK 示例更新 |

### 虚拟人像

| 文档 | URL | 关注点 |
|------|-----|--------|
| 虚拟人像库 | https://www.volcengine.com/docs/82379/2223965 | 新角色、Asset ID |
| 录入真人形象素材 | https://www.volcengine.com/docs/82379/2315856 | 素材要求变更 |
| TOS 数据订阅 | https://www.volcengine.com/docs/6349/2280949 | 订阅格式变更 |

### 数据来源说明

- **1080p 精确像素值**（Seedance 1.0/1.5 系列）：官方文档只声明 "1080P"，未公布精确像素对照表。`ark_media.py` 中的 1080p 像素值（如 1920×1080）基于标准计算推导，非官方明确数据。下次检查时应关注是否有官方像素表发布。
- **Seedance 2.0 确认只支持 480p 和 720p**（来源：2291680 教程页 "输出分辨率 480p, 720p"）
- **Seedance 1.0 pro 确认支持 1080P**（来源：1631633 "影视级美感的 1080P 高清视频"）
- **Seedance 1.5 pro 的 1080p 支持已由官方确认**（来源：控制台模型详情页，分辨率 480P/720P/1080P，帧率 24fps，并发 10，RPM 600）
