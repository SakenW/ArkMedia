# 虚拟人像、已授权真人素材与模型产物二创

## 概述

seedance 2.0 系列**不支持直接上传含有真人人脸的参考图/视频**。平台提供三种替代方案：

| 方案 | 适用场景 |
|------|---------|
| 虚拟人像 | 需真人风格人脸但无需指定具体人物，零合规风险 |
| 已授权真人素材 | 已获得真人授权，需要特定人物 |
| 模型产物二创 | 本账号生成的含人脸视频需再次编辑/延长 |

---

## 使用虚拟人像

平台预置虚拟人像库，提供免费、合规、丰富多样的肖像素材。

**用法：**
1. 浏览虚拟人像库获取 asset ID
2. 在 url 字段传入 `asset://<asset ID>`
3. 提示词中仍需用「图片 n」格式引用

```python
{
    "type": "image_url",
    "image_url": {"url": "asset://asset-20260401123823-6d4x2"},
    "role": "reference_image"
}
```

**案例提示词：**
> 固定机位，近景镜头，清新自然风格。在室内自然光下，`图片1`中美妆博主面带笑容，向镜头介绍`图片2`中的面霜。...

**关键规则：**
- Asset ID 只放在 url 字段
- 提示词中**不能**用 asset ID 指代，必须用「图片 n」
- ✅ 正确：「`图片1`中美妆博主」
- ❌ 错误：「asset-2026****是美妆博主」

---

## 使用已授权真人素材

通过真人认证和本人授权后，可将该真人的图片、视频、音频上传至方舟。素材入库成功后获得 asset ID。

**流程：**
1. 完成真人认证
2. 获得本人授权
3. 上传素材至方舟
4. 获得 asset ID
5. 用 `asset://<asset ID>` 传入

**支持所有模态：**

```python
{"type": "image_url", "image_url": {"url": "asset://<id>"}, "role": "reference_image"}
{"type": "video_url", "video_url": {"url": "asset://<id>"}, "role": "reference_video"}
{"type": "audio_url", "audio_url": {"url": "asset://<id>"}, "role": "reference_audio"}
```

---

## 使用模型产物进行二创

本账号下 seedance 2.0 / 2.0 fast 生成的含人脸原始视频，可直接用于再次编辑/延长。

### 规则

| 场景 | 限制 |
|------|------|
| 含人脸视频 | 仅限本账号近 30 天内 seedance 2.0 系列生成的**原始视频** |
| 不含人脸视频 | 无限制，支持自由剪辑后二次创作 |

### 流程

1. 首次生成视频，获取 video_url
2. 视频原始 URL 有效期 **24 小时**，需先转存（推荐 TOS）
3. 用转存后的 URL 作为 reference_video 再次调用

```python
# 二次编辑：修改面霜颜色
result = client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[
        {"type": "text", "text": "将面霜的颜色修改为白色。"},
        {"type": "video_url", "video_url": {"url": "<转存后的URL>"}, "role": "reference_video"},
    ],
    generate_audio=True,
    ratio="16:9",
    duration=11,
    watermark=True,
)
```

### ⚠️ 注意事项

- 仅信任**原始视频**，二次剪辑后不可用（含人脸场景）
- 仅信任**近 30 天内**生成的视频
- **推荐配置 TOS 数据订阅**自动转存视频产物，避免 URL 过期
