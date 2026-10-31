# Seedream 图像生成 API 参考

## 端点

```
POST https://ark.cn-beijing.volces.com/api/v3/images/generations
```

## Python SDK

```python
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('ARK_API_KEY'),
)

# 基本调用
response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="你的提示词",
    size="2K",
    output_format="png",
    response_format="url",
    watermark=False,
)

# 获取图片 URL
print(response.data[0].url)
```

也兼容 OpenAI SDK：

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('ARK_API_KEY'),
)

response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="你的提示词",
    size="2K",
    output_format="png",
    response_format="url",
    extra_body={"watermark": False},
)
```

## 全参数

```python
client.images.generate(
    model=,                              # string, 必填, Model ID
    prompt=,                             # string, 必填, 提示词（建议 ≤300汉字 / ≤600英文词）
    image=,                              # string 或 list[string], 可选, 参考图 URL
    size=,                               # string, 可选, "2K" / "2048x2048" 等
    output_format=,                      # string, 可选, "png" / "jpeg"（仅5.0）
    response_format=,                    # string, 可选, "url" / "b64_json"
    watermark=,                          # bool, 可选, 是否加水印
    sequential_image_generation=,        # string, 可选, "disabled"(默认) / "auto"(组图)
    sequential_image_generation_options=, # object, 可选, {"max_images": N}
    optimize_prompt_options=,            # object, 可选, {"mode": "standard" / "fast"}
    stream=,                             # bool, 可选, 流式输出
    tools=,                              # array, 可选, [{"type": "web_search"}]
)
```

## 参数详解

### model
替换为对应 Model ID 即可切换模型。详见 [models.md](models.md)。

### prompt
文本提示词。建议不超过 300 汉字或 600 英文单词。

### image
参考图输入：
- **单图：** `image="https://..."` 或 `image="data:image/png;base64,..."`
- **多图：** `image=["https://url1", "https://url2"]`（最多 14 张）
- 不传则为纯文生图

### size
两种方式（不可混用）：
1. 预设分辨率：`"1K"` / `"2K"` / `"3K"` / `"4K"`
2. 精确像素：`"2048x2048"` / `"2848x1600"` 等

### sequential_image_generation
- `"disabled"`（默认）— 单图输出
- `"auto"` — 组图输出（配合 `sequential_image_generation_options.max_images`）

### optimize_prompt_options
```python
optimize_prompt_options={"mode": "fast"}  # 仅 Seedream 4.0 支持 fast
```

### tools（联网搜索）
```python
from volcenginesdkarkruntime.types.images.images import ContentGenerationTool
tools=[ContentGenerationTool(type="web_search")]
```
仅 Seedream 5.0 lite 支持。实际搜索次数通过 `usage.tool_usage.web_search` 返回。

### stream
```python
stream = client.images.generate(..., stream=True)
for event in stream:
    if event.type == "image_generation.partial_succeeded":
        print(f"URL: {event.url}")
    elif event.type == "image_generation.completed":
        print(f"Usage: {event.usage}")
```

流式事件类型（仅 seedream 5.0 lite / 4.5 / 4.0）：
- `image_generation.partial_succeeded` — 单张生成成功（含 url/b64_json/size）
- `image_generation.partial_failed` — 单张生成失败（审核不通过时继续后续，500 异常时中止）
- `image_generation.completed` — 全部完成

## 返回结构

```python
# 非流式
response.data[0].url    # 图片 URL
response.data[0].size   # 图片尺寸
response.data[0].b64_json  # base64（如 response_format="b64_json"）
response.usage          # token 用量
```

## 图片输入要求

| 项目 | 规格 |
|------|------|
| 格式 | jpeg, png, webp, bmp, tiff, gif |
| 传入方式 | URL 或 Base64（`data:image/<format>;base64,<data>`） |
| 宽高比 | [1/16, 16] |
| 最小边长 | > 14 px |
| 大小 | ≤ 10 MB |
| 总像素 | ≤ 36,000,000 |
| 最大数量 | 14 张参考图 |
| 总量约束 | 输入参考图数量 + 输出图片数量 ≤ 15 |

## 数据保存

图片 URL 仅保留 **24 小时**，请及时保存。
