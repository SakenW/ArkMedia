# 模型矩阵与输出规格

## 全系列模型对比

| 模型 | Model ID | 定位 | 分辨率 | 时长 |
|------|----------|------|--------|------|
| seedance 2.0 | `doubao-seedance-2-0-260128` | 最高品质 | 480p, 720p | 4–15s |
| seedance 2.0 fast | `doubao-seedance-2-0-fast-260128` | 更快更省 | 480p, 720p | 4–15s |
| seedance 1.5 pro | `doubao-seedance-1-5-pro-251215` | 高品质+音画同生 | 480p, 720p, 1080p | 4–12s | 24fps |
| seedance 1.0 pro | `doubao-seedance-1-0-pro-250528` | 标准品质 | 480p, 720p, 1080p | 2–12s |
| seedance 1.0 pro fast | `doubao-seedance-1-0-pro-fast-251015` | 快速版 | 480p, 720p, 1080p | 2–12s |
| seedance 1.0 lite i2v | `doubao-seedance-1-0-lite-i2v-250428` | 轻量图生视频 | 480p, 720p, 1080p(参考图不支持) | 2–12s |
| seedance 1.0 lite t2v | `doubao-seedance-1-0-lite-t2v-250428` | 轻量文生视频 | 480p, 720p, 1080p | 2–12s |

## 能力矩阵

| 能力 | 2.0 | 2.0 fast | 1.5 pro | 1.0 pro | 1.0 pro fast | 1.0 lite i2v | 1.0 lite t2v |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 文生视频 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 图生视频-首帧 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 图生视频-首尾帧 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| 多模态参考-图片 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 多模态参考-视频 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 多模态参考-组合 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 编辑视频 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 延长视频 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 生成有声视频 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 联网搜索增强 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 样片模式 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 返回视频尾帧 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 离线推理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 参考图生视频(1-4张) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

## 输出规格

### 宽高比

所有模型通用：`21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`

特殊值：
- `adaptive` — 自动适配（部分场景不支持，见下表）

| 模型 | adaptive 限制 |
|------|--------------|
| seedance 2.0 / 2.0 fast | 全场景支持 |
| seedance 1.5 pro | 全场景支持 |
| seedance 1.0 pro | 文生视频不支持 |
| seedance 1.0 pro fast | 文生视频不支持 |
| seedance 1.0 lite i2v | 参考图和文生视频不支持 |
| seedance 1.0 lite t2v | 文生视频不支持 |

### 各分辨率像素值

**480p：**

| 比例 | seedance 2.0 | seedance 1.5 pro | seedance 1.0 系列 |
|------|-------------|-----------------|------------------|
| 16:9 | 864×496 | 864×496 | 864×480 |
| 4:3 | 752×560 | 752×560 | 736×544 |
| 1:1 | 640×640 | 640×640 | 640×640 |
| 3:4 | 560×752 | 560×752 | 544×736 |
| 9:16 | 496×864 | 496×864 | 480×864 |
| 21:9 | 992×432 | 992×432 | 960×416 |

**720p：**

| 比例 | seedance 2.0 / 1.5 pro | seedance 1.0 系列 |
|------|----------------------|------------------|
| 16:9 | 1280×720 | 1248×704 |
| 4:3 | 1112×834 | 1120×832 |
| 1:1 | 960×960 | 960×960 |
| 3:4 | 834×1112 | 832×1120 |
| 9:16 | 720×1280 | 704×1248 |
| 21:9 | 1470×630 | 1504×640 |

**1080p（seedance 1.5 pro / 1.0 系列，部分不支持）：**

| 比例 | seedance 1.5 pro / 1.0 pro |
|------|---------------------------|
| 16:9 | 1920×1080 / 1920×1088 |
| 4:3 | 1664×1248 |
| 1:1 | 1440×1440 |
| 3:4 | 1248×1664 |
| 9:16 | 1080×1920 / 1088×1920 |
| 21:9 | 2206×946 / 2176×928 |

## 限流

### 在线推理（default）

| 模型 | 个人 RPM | 企业 RPM | 个人并发 | 企业并发 |
|------|---------|---------|---------|---------|
| seedance 2.0 / 2.0 fast | 180 | 600 | 3 | 10 |
| seedance 1.5 pro | — | 600 | — | 10 |
| seedance 1.0 pro / fast | — | 600 | — | 10 |
| seedance 1.0 lite | — | 300 | — | 5 |

### 离线推理（flex）TPD

| 模型 | TPD |
|------|-----|
| seedance 2.0 / 2.0 fast | 无限制 |
| seedance 1.5 pro | 5000亿 |
| seedance 1.0 pro / fast | 5000亿 |
| seedance 1.0 lite | 2500亿 |

## 模型选择指南

| 场景 | 推荐模型 |
|------|---------|
| 最高品质视频 | seedance 2.0 |
| 快速出视频 / 成本敏感 | seedance 2.0 fast |
| 需要 1080p | seedance 1.5 pro |
| 需要样片模式（低成本验证） | seedance 1.5 pro |
| 轻量图生视频 | seedance 1.0 lite i2v |
| 轻量文生视频 | seedance 1.0 lite t2v |
| 多模态参考 / 编辑 / 延长 | seedance 2.0（仅此系列支持） |
| 测试/调试 | seedance 2.0 fast 或 1.0 lite |

## 当前脚本覆盖说明

`ark_media.py` 当前已覆盖：
- 文生视频
- 图生视频首帧
- 图生视频首尾帧
- 参考图输入
- `reference_video`
- `reference_audio`
- 编辑视频 / 延长视频 / 轨道补齐所需的统一 content 结构
- `return_last_frame`
- `web_search`
- `draft_task`（1.5 pro 通过原始参数支持）

当前仍未做成专门高层封装的能力：
- callback_url
- execution_expires_after
- 更细粒度的 draft 工作流助手

这些能力仍可通过直接改脚本扩展，但目前未做成单独 CLI 开关。

## 前置条件

- 火山引擎账号已注册
- API Key：[API Key 管理页面](https://console.volcengine.com/ark/region:ark+cn-beijing/apikey)
- **seedance 2.0 系列需账户余额 ≥ 200 元**
- 也可购买[资源包](https://console.volcengine.com/common-buy/fast/ark_bd%7C%7Cd682ppeeq1mp7kd5q0e0)
- [开通模型](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement)
- 零基础用户可使用[体验中心](https://console.volcengine.com/ark/region:ark+cn-beijing/experience/vision)
- 快速 API 测试可使用 [API Explorer](https://api.volcengine.com/api-explorer/?action=CreateContentsGenerationsTasks&groupName=%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90API&serviceCode=ark&version=2024-01-01)
