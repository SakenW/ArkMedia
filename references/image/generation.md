# Seedream 图像生成模式

## 文生图（纯文本 → 单图）

```python
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="充满活力的特写编辑肖像，模特眼神犀利，头戴雕塑感帽子...",
    size="2K",
    output_format="png",
    watermark=False,
)
```

## 图生图（单图 + 文本 → 单图）

基于已有图片进行编辑：元素增删、风格转化、材质替换、色调迁移、改变背景/视角等。

```python
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="保持模特姿势不变，将服装材质从银色金属改为清水",
    image="https://example.com/input.jpg",
    size="2K",
    output_format="png",
    watermark=False,
)
```

## 多图融合（多图 + 文本 → 单图）

融合多张参考图的风格、元素等特征。如衣裤鞋帽与模特图融合成穿搭图。

```python
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="将图1的服装换为图2的服装",
    image=["https://example.com/model.jpg", "https://example.com/outfit.jpg"],
    sequential_image_generation="disabled",  # 确保单图输出
    size="2K",
    output_format="png",
    watermark=False,
)
```

## 组图生成（多图输出）

需设置 `sequential_image_generation="auto"`。

### 文生组图

```python
from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions

response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="生成一组4张科幻分镜：场景1...场景2...场景3...场景4...",
    size="2K",
    sequential_image_generation="auto",
    sequential_image_generation_options=SequentialImageGenerationOptions(max_images=4),
    output_format="png",
    watermark=False,
)

for image in response.data:
    print(f"URL: {image.url}, Size: {image.size}")
```

### 单图生组图

```python
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="参考这个LOGO，做一套户外运动品牌视觉设计，包括包装袋、帽子、卡片、挂绳等",
    image="https://example.com/logo.png",
    size="2K",
    sequential_image_generation="auto",
    sequential_image_generation_options=SequentialImageGenerationOptions(max_images=4),
    output_format="png",
    watermark=False,
)
```

### 多图生组图

```python
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="生成3张女孩和奶牛玩偶在游乐园的图片，涵盖早晨、中午、晚上",
    image=["https://example.com/girl.png", "https://example.com/cow.png"],
    sequential_image_generation="auto",
    sequential_image_generation_options=SequentialImageGenerationOptions(max_images=3),
    size="2K",
    output_format="png",
    watermark=False,
)
```

## 联网搜索（仅 Seedream 5.0）

```python
from volcenginesdkarkruntime.types.images.images import ContentGenerationTool

response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="制作一张上海未来5日的天气预报图...",
    size="2048x2048",
    tools=[ContentGenerationTool(type="web_search")],
    output_format="png",
    watermark=False,
)
```

## 流式输出

组图生成时可开启流式，生成完任一图片即刻返回：

```python
stream = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="参考图1，生成四张图片...",
    image="https://example.com/ref.png",
    sequential_image_generation="auto",
    sequential_image_generation_options=SequentialImageGenerationOptions(max_images=4),
    stream=True,
    output_format="png",
    watermark=False,
)

for event in stream:
    if event.type == "image_generation.partial_succeeded":
        print(f"完成一张: {event.url}")
    elif event.type == "image_generation.partial_failed":
        print(f"失败: {event.error}")
    elif event.type == "image_generation.completed":
        print(f"全部完成: {event.usage}")
```

## 提示词优化控制

```python
from volcenginesdkarkruntime.types.images.images import OptimizePromptOptions

# Seedream 4.0 支持极速模式
response = client.images.generate(
    model="doubao-seedream-4-0-250828",
    prompt="...",
    optimize_prompt_options=OptimizePromptOptions(mode="fast"),
)
```
