# 使用限制

## 输入限制

### 图片要求

| 项目 | 规格 |
|------|------|
| 传入方式 | URL 或 Base64 编码 |
| 格式 | jpeg, png, webp, bmp, tiff, gif（1.5 pro 新增 heic, heif） |
| 宽高比 | 0.4 ~ 2.5（宽/高） |
| 像素 | 300 ~ 6000 px（宽/高） |
| 大小 | 单张 < 30 MB，请求体 < 64 MB |
| 数量 | 首帧: 1 张 / 首尾帧: 2 张 / 2.0 多模态: 1-9 张 / 1.0 lite 参考: 1-4 张 |

### 视频要求

| 项目 | 规格 |
|------|------|
| 传入方式 | URL 或 `asset://<id>` |
| 格式 | mp4, mov（编码: H.264/AVC, H.265/HEVC; 音频: AAC, MP3） |
| 分辨率 | 480p, 720p |
| 时长 | 单个 [2, 15]s，最多 3 个，总时长 ≤ 15s |
| 宽高比 | [0.4, 2.5] |
| 像素 | [300, 6000] px |
| 总像素数 | [409600, 2086876]（即 [640×640, 2206×946]） |
| 大小 | 单个 < 50 MB |
| 帧率 | 24 ~ 60 FPS |

### 音频要求

| 项目 | 规格 |
|------|------|
| 传入方式 | URL 或 `asset://<id>` |
| 格式 | wav, mp3 |
| 时长 | 单个 [2, 15]s，最多 3 段，总时长 ≤ 15s |
| 大小 | 单个 < 15 MB，请求体 < 64 MB |

### 不支持的输入组合

- ❌ 纯文本 + 音频（无图无视频）
- ❌ 纯音频输入
- ❌ 直接上传含真人人脸的参考图/视频

## 输出限制

见 [models.md](models.md) 的输出规格部分。

## 图片裁剪规则

当指定的视频宽高比与上传图片宽高比不一致时，方舟会居中裁剪：

1. 计算 `Ratio_原始 = W/H`，`Ratio_目标 = A/B`
2. 若 `Ratio_原始 < Ratio_目标`（图太竖）→ 以宽度为基准裁剪
3. 若 `Ratio_原始 > Ratio_目标`（图太横）→ 以高度为基准裁剪
4. 裁剪区域以图片中心为基准

**建议：** 指定的 ratio 与图片实际宽高比尽量接近，效果更好。

## 数据保存

- 任务数据（状态、视频 URL）仅保留 **24 小时**
- Draft 任务 ID 有效期 **7 天**
- 模型产物含人脸视频二创限近 **30 天**

## 素材合规

- 不支持直接上传含真人人脸的参考图/视频
- 含人脸场景需走虚拟人像或已授权真人素材通道（见 portrait-and-creation.md）
- 模型产物二创仅限本账号近 30 天内原始视频（含人脸场景）

## 联网搜索

- 仅适用于纯文本输入
- 会增加时延

## CLI 实际输入能力

- 本地图片：支持，脚本会自动转 data URL
- 远程图片：支持
- `asset://` 图片：支持
- 本地视频：**不支持**
- 本地音频：**不支持**
- 远程视频 / 音频：支持
- `asset://` 视频 / 音频：支持

如需先检查请求体而不提交任务，使用 `--dry-run`。

## 参考链接

- [Video Generation API](https://www.volcengine.com/docs/82379/1520758)
- [API Key 管理](https://console.volcengine.com/ark/region:ark+cn-beijing/apikey)
- [开通模型](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement)
- [体验中心](https://console.volcengine.com/ark/region:ark+cn-beijing/experience/vision)
- [虚拟人像库](https://www.volcengine.com/docs/82379/2223965)
- [录入真人形象素材](https://www.volcengine.com/docs/82379/2315856)
- [视频生成教程](https://www.volcengine.com/docs/82379/2298881)
- [提示词指南](https://www.volcengine.com/docs/82379/2222480)
- [TOS 数据订阅](https://www.volcengine.com/docs/6349/2280949)
