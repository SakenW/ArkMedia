# Seedance 视频生成 API 完整参考

## 端点总览

| 操作 | 方法 | 端点 |
|------|------|------|
| 创建任务 | POST | `/contents/generations/tasks` |
| 查询单个 | GET | `/contents/generations/tasks/{id}` |
| 查询列表 | GET | `/contents/generations/tasks?page_num=&page_size=&filter.status=&filter.task_ids=&filter.model=` |
| 取消/删除 | DELETE | `/contents/generations/tasks/{id}` |

**Base URL:** `https://ark.cn-beijing.volces.com/api/v3`
**认证:** `Authorization: Bearer $ARK_API_KEY`

---

## 创建视频生成任务

### 请求参数

#### model (string, 必选)
模型 ID 或 Endpoint ID。

#### content (object[], 必选)
输入内容数组，支持以下类型组合：
- 文本
- 文本（可选）+ 图片
- 文本（可选）+ 视频
- 文本（可选）+ 图片 + 音频
- 文本（可选）+ 图片 + 视频
- 文本（可选）+ 视频 + 音频
- 文本（可选）+ 图片 + 视频 + 音频
- 样片任务 ID

**text 对象：**
```json
{"type": "text", "text": "提示词（≤500汉字 / ≤1000英文词）"}
```

**image_url 对象：**
```json
{"type": "image_url", "image_url": {"url": "https://..."}, "role": "first_frame|last_frame|reference_image"}
```
- `first_frame` — 图生视频首帧（或不填 role）
- `last_frame` — 图生视频尾帧（必须配 first_frame）
- `reference_image` — 参考图（Seedance 2.0: 1~9 张，Seedance 1.0 lite i2v: 1~4 张）

图片要求：
- 格式：jpeg, png, webp, bmp, tiff, gif（1.5 pro 额外 heic/heif）
- 宽高比：(0.4, 2.5)
- 像素：(300, 6000)
- 大小：< 30 MB
- URL / Base64 / 素材 ID (`asset://<ASSET_ID>`)

**video_url 对象：**（仅 Seedance 2.0）
```json
{"type": "video_url", "video_url": {"url": "https://..."}, "role": "reference_video"}
```
- 格式：mp4, mov
- 分辨率：480p, 720p
- 时长：[2, 15]s，最多 3 个，总计 ≤ 15s
- 帧率：[24, 60]

**audio_url 对象：**（仅 Seedance 2.0）
```json
{"type": "audio_url", "audio_url": {"url": "https://..."}, "role": "reference_audio"}
```
- 格式：wav, mp3
- 时长：[2, 15]s，最多 3 段，总计 ≤ 15s
- 大小：< 15 MB

**draft_task 对象：**（仅 Seedance 1.5 pro）
```json
{"type": "draft_task", "draft_task": {"id": "cgt-xxx"}}
```

#### callback_url (string, 可选)
任务状态变化时的回调地址。回调状态：queued / running / succeeded / failed / expired。

#### return_last_frame (boolean, 默认 false)
返回尾帧图像（png），可用于连续视频生成。

#### service_tier (string, 默认 "default")
- `default` — 在线推理
- `flex` — 离线推理（价格 50%）

#### execution_expires_after (integer, 默认 172800)
任务超时阈值（秒），范围 [3600, 259200]。

#### generate_audio (boolean, 默认 true)
仅 Seedance 2.0 & 1.5 pro。是否生成有声视频。

#### draft (boolean, 默认 false)
仅 Seedance 1.5 pro。开启样片模式（480p 预览）。

#### tools (object[], 仅 Seedance 2.0)
```json
[{"type": "web_search"}]
```

#### resolution (string)
- 480p, 720p, 1080p（1.0 lite 参考图、2.0 不支持 1080p）
- Seedance 2.0/1.5 pro/1.0 lite 默认 720p
- Seedance 1.0 pro/pro-fast 默认 1080p

#### ratio (string)
16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive

#### duration (integer, 默认 5)
- Seedance 1.0 系列：[2, 12]
- Seedance 1.5 pro：[4, 12] 或 -1（智能）
- Seedance 2.0：[4, 15] 或 -1（智能）

#### frames (integer)
1.0 系列专用。公式：帧数 = 时长 × 24。范围 [29, 289]，格式 25+4n。

#### seed (integer, 默认 -1)
随机种子，范围 [-1, 2^32-1]。

#### camera_fixed (boolean, 默认 false)
参考图场景不支持，2.0 不支持。

#### watermark (boolean, 默认 false)

#### safety_identifier (string, 可选)
终端用户唯一标识。

### 响应

```json
{
  "id": "cgt-2025xxxx-xxxx",
  "model": "doubao-seedance-2-0-260128",
  "status": "queued",
  "created_at": 1743414619
}
```

**任务 ID 仅保留 7 天。**

---

## 查询单个任务

```
GET /contents/generations/tasks/{id}
```

### 响应

```json
{
  "id": "cgt-2025xxxx-xxxx",
  "model": "doubao-seedance-1-5-pro-251215",
  "status": "succeeded",
  "content": {
    "video_url": "https://...",
    "last_frame_url": "https://..."
  },
  "usage": {
    "completion_tokens": 108900,
    "total_tokens": 108900
  },
  "created_at": 1743414619,
  "updated_at": 1743414673,
  "seed": 10,
  "resolution": "720p",
  "ratio": "16:9",
  "duration": 5,
  "framespersecond": 24,
  "service_tier": "default",
  "generate_audio": true,
  "draft": false
}
```

**状态值：** queued / running / cancelled / succeeded / failed / expired

**视频 URL 24h 过期，请及时保存。**

---

## 查询任务列表

```
GET /contents/generations/tasks?page_num=1&page_size=10&filter.status=succeeded
```

### 请求参数（Query String）

| 参数 | 类型 | 说明 |
|------|------|------|
| page_num | integer [1,500] | 页码 |
| page_size | integer [1,500] | 每页数量 |
| filter.status | string | queued/running/cancelled/succeeded/failed/expired |
| filter.task_ids | string[] | 精确搜索多个任务 ID |
| filter.model | string | 推理接入点 ID |
| filter.service_tier | string | default / flex |

### 响应

```json
{
  "total": 3,
  "items": [
    {
      "id": "cgt-xxxx",
      "model": "doubao-seedance-1-5-pro-251215",
      "status": "succeeded",
      "content": {"video_url": "https://..."},
      "usage": {"completion_tokens": 108900, "total_tokens": 108900},
      ...
    }
  ]
}
```

**仅支持最近 7 天数据。**

---

## 取消/删除任务

```
DELETE /contents/generations/tasks/{id}
```

### 行为

| 当前状态 | 支持DELETE | 操作 |
|---------|:---:|------|
| queued | ✅ | 取消排队 → cancelled |
| running | ❌ | — |
| succeeded | ✅ | 删除记录 |
| failed | ✅ | 删除记录 |
| cancelled | ❌ | — |
| expired | ✅ | 删除记录 |

### 响应

```json
{}
```

---

## 宽高比像素值

### Seedance 2.0 & 2.0 fast

| ratio | 480p | 720p |
|-------|------|------|
| 16:9 | 864×496 | 1280×720 |
| 4:3 | 752×560 | 1112×834 |
| 1:1 | 640×640 | 960×960 |
| 3:4 | 560×752 | 834×1112 |
| 9:16 | 496×864 | 720×1280 |
| 21:9 | 992×432 | 1470×630 |

### Seedance 1.5 pro

| ratio | 480p | 720p | 1080p |
|-------|------|------|-------|
| 16:9 | 864×480 | 1248×704 | 1920×1080 |
| 4:3 | 736×544 | 1120×832 | 1664×1248 |
| 1:1 | 640×640 | 960×960 | 1440×1440 |
| 3:4 | 544×736 | 832×1120 | 1248×1664 |
| 9:16 | 480×864 | 704×1248 | 1080×1920 |
| 21:9 | 960×416 | 1504×640 | 2206×946 |

### Seedance 1.0 系列

同 Seedance 1.5 pro 像素值。lite 参考图场景不支持 1080p。
