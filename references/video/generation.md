# 视频生成基础模式

> 本文件只描述 `ark-media` 已支持或可直接映射的执行层能力。
> 上层剧情、分镜、continuity、项目脚手架不属于这里。

覆盖所有 seedance 模型的通用视频生成方式。

## 文生视频（Text-to-Video）

纯文本提示词生成视频，结果随机性较大，适合激发灵感。

```python
client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[
        {"type": "text", "text": "写实风格，晴朗的蓝天之下，一大片白色的雏菊花田，镜头逐渐拉近，最终定格在一朵雏菊花的特写上，花瓣上有几颗晶莹的露珠"}
    ],
    ratio="16:9",
    duration=5,
    watermark=True,
)
```

**提示词建议：**
- 提示词 = 主体+运动，背景+运动，镜头+运动
- 用简洁准确的自然语言
- 建议先用生图模型生成满意图片，再图生视频
- 不符合预期时：抽象描述换具象描述，删除不重要部分，重要内容前置

**CLI：**
```bash
python scripts/ark_media.py generate-video "写实风格，晴朗的蓝天之下，一大片白色的雏菊花田，镜头逐渐拉近，最终定格在一朵雏菊花的特写上" \
  --model seedance-2.0 --resolution 480p --ratio 16:9 --duration 5
```

## 图生视频 — 首帧（Image-to-Video, First Frame）

指定首帧图片，基于该图生成连贯视频。seedance 2.0 / 1.5 pro 支持 `generate_audio=True` 生成有声视频。

```python
client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[
        {"type": "text", "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头..."},
        {"type": "image_url", "image_url": {"url": "<首帧图片URL>"}}
        # 不指定 role 时默认为首帧
    ],
    generate_audio=True,
    ratio="adaptive",
    duration=5,
    watermark=True,
)
```

**要点：**
- 上传高质量图片，图片质量对视频效果影响很大
- 不指定 `role` 时图片默认作为首帧

**CLI：**
```bash
python scripts/ark_media.py generate-video "女孩抱着狐狸，温柔地看向镜头，镜头缓缓拉出" \
  --model seedance-2.0 --resolution 480p --ratio adaptive --duration 5 \
  --image /path/to/first-frame.png
```

## 图生视频 — 首尾帧（Image-to-Video, First + Last Frame）

指定首帧和尾帧图片，模型生成流畅衔接的视频。

```python
client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[
        {"type": "text", "text": "图中女孩对着镜头说'茄子'，360度环绕运镜"},
        {"type": "image_url", "image_url": {"url": "<首帧URL>"}, "role": "first_frame"},
        {"type": "image_url", "image_url": {"url": "<尾帧URL>"}, "role": "last_frame"},
    ],
    generate_audio=True,
    ratio="adaptive",
    duration=5,
    watermark=True,
)
```

**CLI：**
```bash
python scripts/ark_media.py generate-video "图中女孩对着镜头说'茄子'，360度环绕运镜" \
  --model seedance-2.0 --resolution 480p --ratio adaptive --duration 5 \
  --image /path/to/first-frame.png --last-frame /path/to/last-frame.png
```

## 图生视频 — 参考图（Reference Images）

提供 1-4 张参考图，模型提取关键特征，生成与参考图视觉风格一致的视频。

```python
client.content_generation.tasks.create(
    model="doubao-seedance-1-0-lite-i2v-250428",
    content=[
        {"type": "text", "text": "[图1]戴着眼镜穿着蓝色T恤的男生和[图2]的柯基小狗，坐在[图3]的草坪上"},
        {"type": "image_url", "image_url": {"url": "<图1>"}, "role": "reference_image"},
        {"type": "image_url", "image_url": {"url": "<图2>"}, "role": "reference_image"},
        {"type": "image_url", "image_url": {"url": "<图3>"}, "role": "reference_image"},
    ],
    ratio="16:9",
    duration=5,
    watermark=True,
)
```

**注意：**
- 参考图模式目前仅 seedance 1.0 lite i2v 和 seedance 2.0 支持
- seedance 2.0 的多模态参考支持最多 9 张图片（详见 multimodal-input.md）

**CLI：**
```bash
python scripts/ark_media.py generate-video "[图1]戴着眼镜穿着蓝色T恤的男生和[图2]的柯基小狗，坐在[图3]的草坪上" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 5 \
  --reference-images /path/to/ref1.png /path/to/ref2.png /path/to/ref3.png
```

## 多模态参考（Seedance 2.0）

Seedance 2.0 / 2.0 fast 支持将文本、图片、视频、音频组合后生成新视频。

**CLI：**
```bash
python scripts/ark_media.py generate-video "参考视频1的运镜，参考图片1的人物形象，参考音频1的背景音乐生成广告片" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 8 \
  --reference-images https://example.com/lead.png \
  --reference-videos https://example.com/cam-ref.mp4 \
  --reference-audios https://example.com/bgm.mp3 \
  --input-duration 6
```

说明：
- `--reference-images` 支持现有本地图片、URL、`asset://`
- `--reference-videos` / `--reference-audios` 仅支持 URL 或 `asset://`
- 使用 `--reference-videos` 时建议传 `--input-duration`，便于费用估算

## 连续视频生成

用前一个视频的尾帧作为下一个的首帧，循环生成连续视频。

```python
def generate_video_with_last_frame(prompt, initial_image_url=None):
    content = [{"text": prompt, "type": "text"}]
    if initial_image_url:
        content.append({"image_url": {"url": initial_image_url}, "type": "image_url"})

    result = client.content_generation.tasks.create(
        model="doubao-seedance-2-0-260128",
        content=content,
        return_last_frame=True,  # 关键：返回尾帧
        ratio="adaptive",
        duration=5,
        watermark=False,
    )
    # ... 轮询 ...
    return video_url, last_frame_url

# 链式调用
url, last_frame = generate_video_with_last_frame("第一个场景", initial_image)
url2, last_frame2 = generate_video_with_last_frame("第二个场景", last_frame)
url3, _ = generate_video_with_last_frame("第三个场景", last_frame2)
```

**CLI：**
```bash
python scripts/ark_media.py generate-video "第一个场景" \
  --model seedance-2.0 --resolution 480p --ratio adaptive --duration 5 \
  --image /path/to/initial.png --return-last-frame
```

然后：
1. 轮询任务
2. 自动下载视频和尾帧到 `~/Downloads`
3. 将尾帧作为下一段的 `--image`

注意：
- 这只是链式生成，不是模型级无缝拼接
- 真正编辑/延长/轨道补齐请优先走 `reference_video` 流程

## dry run 联调

调试参数组合时，先用 `--dry-run` 打印最终请求体，避免直接扣费：

```bash
python scripts/ark_media.py generate-video "视频1中的拱形窗户打开，进入美术馆室内，接视频2" \
  --model seedance-2.0 --reference-videos https://example.com/v1.mp4 https://example.com/v2.mp4 \
  --duration 8 --input-duration 10 --dry-run
```

## 样片模式（仅 seedance 1.5 pro）

两步走，低成本验证后再出正片。

### Step 1: 生成 Draft

```python
client.content_generation.tasks.create(
    model="doubao-seedance-1-5-pro-251215",
    content=[...],
    seed=20,
    duration=6,
    draft=True,  # 样片模式
)
```

- 仅支持 480p
- token 消耗约正常的 0.6 倍
- 不支持返回尾帧、离线推理

### Step 2: Draft → 正式

```python
client.content_generation.tasks.create(
    model="doubao-seedance-1-5-pro-251215",
    content=[
        {"type": "draft_task", "draft_task": {"id": "cgt-2026****-pzjqb"}}
    ],
    watermark=False,
    resolution="720p",
    return_last_frame=True,
    service_tier="default",
)
```

- 自动复用 Draft 的 model、content、seed、ratio、duration 等
- Draft 任务 ID 有效期 7 天
