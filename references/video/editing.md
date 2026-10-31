# 视频编辑：增删改 / 延长 / 轨道补齐

> 本文件只关心执行层输入，不负责上层创作决策。
> 你应该先准备好可执行的视频、图片、音频素材，再交给 `ark-media`。

## 5.1 元素增删改

提供待编辑的视频 + 参考图/音频 + 提示词，完成替换主体、增删对象、局部重绘等。

### 增加元素

**模板：**
```
在「视频n」的「时间位置」+「空间位置」，增加「理想元素描述」。
```

**案例：**
> 在`视频1`的台面上添加炸鸡、披萨等小吃。

### 删除元素

**模板：**
```
删除「视频n」中的「被删除元素」，视频其他内容保持不变。
```

**案例：**
> 清除`视频1`桌面上的其他零件和工具，保持桌面整洁干净，桌面上只有他俩手里的。

### 修改元素

**模板：**
```
将「视频n」中的「被更换元素描述」，替换为「理想元素描述」。
```

**案例：**
> 将`视频1`中的香水替换成`图片1`中的面霜，动作和运镜不变。

### 编辑要点

- 不变的部分可在提示词中强调保持，效果更好
- 可同时参考图片来提供替换元素的具体形象

**CLI：**
```bash
python scripts/ark_media.py generate-video "将视频1中的香水替换成图片1中的面霜，动作和运镜不变" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 5 \
  --reference-videos https://example.com/input.mp4 \
  --reference-images https://example.com/cream.png \
  --input-duration 5
```

---

## 5.2 视频延长

在原有视频基础上，向前或者向后延长。

**模板：**
```
- 向前/向后延长「视频n」+「需延长的视频描述」
- 生成「视频n」之前/之后的内容 +「需延长的视频描述」
```

### 向后延长

**案例：**
> 生成`视频1`之后的内容，迟到的两个男士跑向他们，五个人终于见面，友好聊天。

### 向前延长

**案例：**
> 向前延长`视频1`，给白衣男子过肩镜头，白衣男子说："It's not that bad. You're just stressed."

### 延长要点

- 生成的视频一般只包含原视频的尾部/头部画面，但可通过提示词控制
- 例如：向前延长视频1，[延长内容描述...]，**最后接视频1**
- 模型自动截取衔接部分合成，输入视频原有片段不会重复生成

**CLI：**
```bash
python scripts/ark_media.py generate-video "生成视频1之后的内容，迟到的两个男士跑向他们，五个人终于见面，友好聊天" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 8 \
  --reference-videos https://example.com/v1.mp4 \
  --input-duration 5
```

---

## 5.3 轨道补齐（多段串联）

传入 2–3 段视频，自动补全中间过渡，生成包含原视频 + 新内容的完整视频。

**模板：**
```
「视频1」+「过渡画面描述」+ 接「视频2」+「过渡画面描述」+ 接「视频3」
```

**案例：**
> `视频1`，树叶落地的瞬间，激起金色粒子特效，一阵风吹过，接`视频2`。

### 限制

- 最多 3 段视频输入
- 总时长不得超过 15 秒
- 生成时自动截取首尾视频的衔接部分，仅保留必要片段参与合成

**CLI：**
```bash
python scripts/ark_media.py generate-video "视频1，树叶落地的瞬间，激起金色粒子特效，一阵风吹过，接视频2" \
  --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 8 \
  --reference-videos https://example.com/v1.mp4 https://example.com/v2.mp4 \
  --input-duration 10
```

---

## API 调用模式

所有编辑/延长/补齐都通过同一个 API：

```python
client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[
        {"type": "text", "text": "编辑/延长/补齐的提示词"},
        {"type": "video_url", "video_url": {"url": "<url>"}, "role": "reference_video"},
        # 可选：加入图片参考
        # {"type": "image_url", "image_url": {"url": "<url>"}, "role": "reference_image"},
    ],
    generate_audio=True,
    ratio="16:9",
    duration=8,   # 最终输出时长
    watermark=True,
)
```

区别在于提示词和 content 的组合不同，API 调用方式统一。

## 输入提醒

- `reference_video` / `reference_audio` 当前仅支持公网 URL 或 `asset://<id>`
- 本地视频和本地音频不能直接传给脚本
- 若不确定最终 body，先加 `--dry-run`
