#!/usr/bin/env python3
"""
Ark Media Helper — 火山方舟图像/视频生成 + 费用估算

用法:
  python ark_media.py generate-image "提示词" --model seedream-5.0 --size 2K
  python ark_media.py generate-video "提示词" --model seedance-2.0 --resolution 720p
  python ark_media.py poll <task_id>
  python ark_media.py cost image --model seedream-5.0 --count 4
  python ark_media.py cost video --model seedance-2.0 --resolution 720p --ratio 16:9 --duration 5
  python ark_media.py list-tasks --status succeeded --page-size 5
  python ark_media.py cancel <task_id>

依赖: pip install 'volcengine-python-sdk[ark]'
"""

import argparse
import base64
import json
import math
import os
import sys
import time
from typing import Optional
from urllib.parse import urlparse
from urllib.error import HTTPError

# Fix broken venv: ensure site-packages is on sys.path
_venv_site = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'lib', 'python3.14', 'site-packages')
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

# ── 定价数据 ──────────────────────────────────────────────

IMAGE_PRICING = {
    # model_id_suffix: yuan_per_image
    "seedream-5-0-260128": 0.22,
    "seedream-5-0-lite-260128": 0.22,
    "seedream-4-5-251128": 0.25,
    "seedream-4-0-250828": 0.20,
    "seedream-3-0-t2i-250415": 0.259,
}

VIDEO_PRICING = {
    # (model_id_suffix, has_video_input): yuan_per_million_tokens
    ("seedance-2-0-260128", False): 46.0,
    ("seedance-2-0-260128", True): 28.0,
    ("seedance-2-0-fast-260128", False): 37.0,
    ("seedance-2-0-fast-260128", True): 22.0,
}

VIDEO_PRICING_SIMPLE = {
    # model_id_suffix: {"online": {"audio": 16.0, "no_audio": 8.0}, "offline": {...}}
    "seedance-1-5-pro-251215": {
        "online": {"audio": 16.0, "no_audio": 8.0},
        "offline": {"audio": 8.0, "no_audio": 4.0},
    },
    "seedance-1-0-pro-250528": {"online": 15.0, "offline": 7.5},
    "seedance-1-0-pro-fast-251015": {"online": 4.2, "offline": 2.1},
    "seedance-1-0-lite-t2v-250428": {"online": 10.0, "offline": 5.0},
    "seedance-1-0-lite-i2v-250428": {"online": 10.0, "offline": 5.0},
}

# Seedance 2.0 最低 token 用量限制 (16:9)
MIN_TOKENS_2_0 = {
    # duration_seconds: {resolution: min_tokens}
    4: {"480p": 70308, "720p": 151200},
    5: {"480p": 90396, "720p": 194400},
    6: {"480p": 100440, "720p": 216000},
    7: {"480p": 120528, "720p": 259200},
    8: {"480p": 140616, "720p": 302400},
    9: {"480p": 150660, "720p": 324000},
    10: {"480p": 170748, "720p": 367200},
    11: {"480p": 190836, "720p": 410400},
    12: {"480p": 200880, "720p": 432000},
    13: {"480p": 220968, "720p": 475200},
    14: {"480p": 241056, "720p": 518400},
    15: {"480p": 251100, "720p": 540000},
}

VIDEO_PIXELS = {
    # (resolution, ratio): (w, h) — Seedance 2.0 & 2.0 fast
    ("720p", "16:9"): (1280, 720),
    ("720p", "4:3"): (1112, 834),
    ("720p", "1:1"): (960, 960),
    ("720p", "3:4"): (834, 1112),
    ("720p", "9:16"): (720, 1280),
    ("720p", "21:9"): (1470, 630),
    ("480p", "16:9"): (864, 496),
    ("480p", "4:3"): (752, 560),
    ("480p", "1:1"): (640, 640),
    ("480p", "3:4"): (560, 752),
    ("480p", "9:16"): (496, 864),
    ("480p", "21:9"): (992, 432),
    # Seedance 1.5 pro / 1.0 series — 1080p
    ("1080p", "16:9"): (1920, 1080),
    ("1080p", "4:3"): (1664, 1248),
    ("1080p", "1:1"): (1440, 1440),
    ("1080p", "3:4"): (1248, 1664),
    ("1080p", "9:16"): (1080, 1920),
    ("1080p", "21:9"): (2206, 946),
    # Seedance 1.5 pro / 1.0 series — 480p / 720p (slightly different from 2.0)
    # Use 2.0 values as approximation — difference is <5%
}

# ── 模型名称简写映射 ──────────────────────────────────────

MODEL_ALIASES = {
    # Image
    "seedream-5.0": "doubao-seedream-5-0-260128",
    "seedream-5.0-lite": "doubao-seedream-5-0-lite-260128",
    "seedream-4.5": "doubao-seedream-4-5-251128",
    "seedream-4.0": "doubao-seedream-4-0-250828",
    "seedream-3.0": "doubao-seedream-3-0-t2i-250415",
    # Video
    "seedance-2.0": "doubao-seedance-2-0-260128",
    "seedance-2.0-fast": "doubao-seedance-2-0-fast-260128",
    "seedance-1.5": "doubao-seedance-1-5-pro-251215",
    "seedance-1.0": "doubao-seedance-1-0-pro-250528",
    "seedance-1.0-fast": "doubao-seedance-1-0-pro-fast-251015",
    "seedance-1.0-lite-t2v": "doubao-seedance-1-0-lite-t2v-250428",
    "seedance-1.0-lite-i2v": "doubao-seedance-1-0-lite-i2v-250428",
}


def local_image_to_data_url(path: str) -> str:
    """将本地图片转为 data:image/xxx;base64,... 格式。
    支持 jpeg/png/webp/bmp/tiff/gif。
    限制：≤10MB, 宽高比 [1/16, 16], 像素积 ≤36M。
    """
    ext = path.lower().rsplit('.', 1)[-1] if '.' in path else 'png'
    fmt_map = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'webp': 'webp',
               'bmp': 'bmp', 'tiff': 'tiff', 'tif': 'tiff', 'gif': 'gif'}
    fmt = fmt_map.get(ext, 'png')
    size = os.path.getsize(path)
    if size > 10 * 1024 * 1024:
        raise ValueError(f"图片太大: {size//1024//1024}MB (限制 10MB)")
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/{fmt};base64,{b64}"


def _is_remote_or_asset_url(value: str) -> bool:
    if value.startswith("asset://"):
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def _normalize_visual_input(path_or_url: str, allow_local_file: bool = True) -> str:
    """标准化图片输入：本地图片转 data url，其余保留原值。"""
    if allow_local_file and os.path.exists(path_or_url):
        return local_image_to_data_url(path_or_url)
    if _is_remote_or_asset_url(path_or_url):
        return path_or_url
    raise ValueError(
        f"图片输入必须是现有本地文件、公网 URL 或 asset://<id>: {path_or_url}"
    )


def _normalize_remote_input(path_or_url: str, *, kind: str) -> str:
    """校验视频/音频输入必须为公网 URL 或 asset://。"""
    if os.path.exists(path_or_url):
        raise ValueError(
            f"{kind} 暂不支持本地文件直传: {path_or_url}。请先上传到公网 URL 或使用 asset://<id>"
        )
    if not _is_remote_or_asset_url(path_or_url):
        raise ValueError(
            f"{kind} 必须是公网 URL 或 asset://<id>: {path_or_url}"
        )
    return path_or_url


def resolve_model(name: str) -> str:
    """将简写名称解析为完整 model ID。"""
    if name.startswith("doubao-"):
        return name
    if name in MODEL_ALIASES:
        return MODEL_ALIASES[name]
    # 尝试模糊匹配
    for alias, full_id in MODEL_ALIASES.items():
        if alias.replace(".", "-").replace("-", "") == name.replace(".", "-").replace("-", ""):
            return full_id
    raise ValueError(f"未知模型: {name}。可用: {', '.join(MODEL_ALIASES.keys())}")


# ── 费用估算 ──────────────────────────────────────────────

def estimate_image_cost(model_id: str, count: int = 1) -> float:
    """估算图像生成费用（元）。"""
    for suffix, price in IMAGE_PRICING.items():
        if model_id.endswith(suffix):
            return price * count
    raise ValueError(f"未知图像模型定价: {model_id}")


def estimate_video_tokens(
    resolution: str, ratio: str, duration: int, input_duration: int = 0
) -> int:
    """估算视频 token 用量。"""
    pixels = VIDEO_PIXELS.get((resolution, ratio))
    if not pixels:
        raise ValueError(f"未知分辨率/比例组合: {resolution} {ratio}")
    w, h = pixels
    fps = 24
    tokens = (input_duration + duration) * w * h * fps // 1024
    return tokens


def estimate_video_cost(
    model_id: str,
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    input_duration: int = 0,
    has_audio: bool = True,
    service_tier: str = "online",
) -> dict:
    """估算视频生成费用（元）。返回 {tokens, yuan, note}。"""
    tokens = estimate_video_tokens(resolution, ratio, duration, input_duration)

    # Seedance 2.0 系列
    for suffix in ["seedance-2-0-260128", "seedance-2-0-fast-260128"]:
        if model_id.endswith(suffix):
            has_video_input = input_duration > 0
            price_per_m = VIDEO_PRICING.get((suffix, has_video_input))
            if not price_per_m:
                raise ValueError(f"未知定价: {suffix}")
            # 最低 token 限制
            min_tokens = MIN_TOKENS_2_0.get(duration, {}).get(resolution, 0)
            if has_video_input and min_tokens > 0 and tokens < min_tokens:
                tokens = min_tokens
            cost = tokens / 1_000_000 * price_per_m
            note = f"{'含视频输入' if has_video_input else '无视频输入'}"
            if has_video_input and min_tokens:
                note += f", 最低token={min_tokens}"
            return {"tokens": tokens, "yuan": round(cost, 2), "note": note}

    # Seedance 1.5 pro
    if model_id.endswith("seedance-1-5-pro-251215"):
        pricing = VIDEO_PRICING_SIMPLE["seedance-1-5-pro-251215"]
        tier_pricing = pricing[service_tier]
        if isinstance(tier_pricing, dict):
            key = "audio" if has_audio else "no_audio"
            price_per_m = tier_pricing[key]
        else:
            price_per_m = tier_pricing
        cost = tokens / 1_000_000 * price_per_m
        audio_note = "有声" if has_audio else "无声"
        return {"tokens": tokens, "yuan": round(cost, 2), "note": f"{service_tier} {audio_note}"}

    # Seedance 1.0 系列
    for suffix, pricing in VIDEO_PRICING_SIMPLE.items():
        if model_id.endswith(suffix) and suffix != "seedance-1-5-pro-251215":
            tier_pricing = pricing[service_tier]
            cost = tokens / 1_000_000 * tier_pricing
            return {"tokens": tokens, "yuan": round(cost, 2), "note": f"{service_tier}"}

    raise ValueError(f"未知视频模型定价: {model_id}")


# ── API 客户端 ─────────────────────────────────────────────

def get_client():
    """获取 Ark SDK 客户端。"""
    try:
        from volcenginesdkarkruntime import Ark
    except ImportError:
        print("请先安装 SDK: pip install 'volcengine-python-sdk[ark]'", file=sys.stderr)
        sys.exit(1)
    return Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.getenv("ARK_API_KEY"),
    )


def _default_output_dir() -> str:
    """默认输出目录：用户下载文件夹。"""
    d = os.path.expanduser("~/Downloads")
    os.makedirs(d, exist_ok=True)
    return d


def _download_image(url: str, path: str) -> str:
    """下载图片到本地，返回实际保存路径。"""
    import urllib.request
    urllib.request.urlretrieve(url, path)
    return path


def generate_image(
    prompt: str,
    model: str = "seedream-5.0",
    size: str = "2K",
    image: Optional[str] = None,
    images: Optional[list] = None,
    output_format: str = "png",
    sequential: str = "disabled",
    max_images: int = 1,
    watermark: bool = False,
    stream: bool = False,
    output_dir: Optional[str] = None,
):
    """生成图像。返回本地文件路径列表（默认保存到 ~/Downloads）。
    
    支持：
    - 文生图（无参考图）
    - 单图编辑（image=单张路径/URL）
    - 多图融合（images=[路径1, 路径2, ...]）
    - 组图生成（sequential=auto, max_images=2~4）
    """
    client = get_client()
    model_id = resolve_model(model)

    from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions

    kwargs = {
        "model": model_id,
        "prompt": prompt,
        "size": size,
        "output_format": output_format,
        "response_format": "url",
        "watermark": watermark,
        "sequential_image_generation": sequential,
        "stream": stream,
    }
    
    # 合并 image 和 images 为统一列表
    img_list = []
    if image:
        img_list.append(image)
    if images:
        img_list.extend(images)
    
    if len(img_list) == 1:
        # 单张参考图
        p = img_list[0]
        if os.path.exists(p):
            p = local_image_to_data_url(p)
        kwargs["image"] = p
    elif len(img_list) > 1:
        # 多张参考图（多图融合 / 多图生组图）
        converted = []
        for p in img_list:
            if os.path.exists(p):
                p = local_image_to_data_url(p)
            converted.append(p)
        kwargs["image"] = converted
    if sequential == "auto":
        kwargs["sequential_image_generation_options"] = SequentialImageGenerationOptions(
            max_images=max_images
        )

    # 先估算费用
    count = max_images if sequential == "auto" else 1
    cost = estimate_image_cost(model_id, count)
    print(f"📋 模型: {model_id} | 预估费用: ¥{cost:.2f} ({count}张)", file=sys.stderr)

    resp = client.images.generate(**kwargs)

    if stream:
        urls = []
        for event in resp:
            if event.type == "image_generation.partial_succeeded" and event.url:
                urls.append(event.url)
                print(f"  ✅ 完成: {event.url}", file=sys.stderr)
            elif event.type == "image_generation.completed":
                print(f"  📊 Usage: {event.usage}", file=sys.stderr)
        return urls
    else:
        urls = [img.url for img in resp.data]
        outdir = output_dir or _default_output_dir()
        local_paths = []
        for i, url in enumerate(urls):
            ext = output_format if output_format != "jpg" else "jpeg"
            fname = f"ark_img_{model_id}_{int(time.time())}_{i}.{ext}"
            fpath = os.path.join(outdir, fname)
            try:
                _download_image(url, fpath)
                print(f"  ✅ 图{i+1}: {fpath}", file=sys.stderr)
                local_paths.append(fpath)
            except Exception as e:
                print(f"  ⚠️ 图{i+1} 下载失败: {e}, URL: {url}", file=sys.stderr)
                local_paths.append(url)

    # ── 最终摘要 ──
    _print_summary(
        kind="image", model=model, model_id=model_id,
        cost=cost, count=len(local_paths), outputs=local_paths,
        extra={"size": size, "format": output_format},
    )
    return local_paths


def _print_summary(
    kind: str,
    model: str,
    model_id: str,
    cost: float,
    count: int,
    outputs: list,
    extra: dict = None,
):
    """统一输出最终摘要（stdout，供 agent 读取）。"""
    summary = {
        "type": kind,
        "model": model,
        "model_id": model_id,
        "cost_yuan": round(cost, 2),
        "count": count,
        "outputs": outputs,
    }
    if extra:
        summary.update(extra)
    print(f"\n{'='*50}")
    print(f"🎨 {kind.upper()} 生成完成")
    print(f"{'='*50}")
    print(f"  模型:     {model} ({model_id})")
    print(f"  费用:     ¥{cost:.2f}")
    print(f"  数量:     {count} 张/个")
    if kind == "image" and extra:
        print(f"  尺寸:     {extra.get('size', '?')}")
        print(f"  格式:     {extra.get('format', '?')}")
    elif kind == "video" and extra:
        print(f"  分辨率:   {extra.get('resolution', '?')}")
        print(f"  时长:     {extra.get('duration', '?')}s")
        print(f"  比例:     {extra.get('ratio', '?')}")
    print(f"  输出:")
    for o in outputs:
        print(f"    📄 {o}")
    print(f"{'='*50}\n")
    # JSON for machine readability
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _video_headers() -> dict:
    """视频 API 请求头。"""
    return {
        "Authorization": f"Bearer {os.getenv('ARK_API_KEY')}",
        "Content-Type": "application/json",
    }


def generate_video(
    prompt: str,
    model: str = "seedance-2.0",
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    image_url: Optional[str] = None,
    image_role: str = "first_frame",
    last_frame_url: Optional[str] = None,
    reference_images: Optional[list] = None,
    reference_videos: Optional[list] = None,
    reference_audios: Optional[list] = None,
    generate_audio: bool = True,
    return_last_frame: bool = False,
    service_tier: str = "default",
    watermark: bool = False,
    seed: int = -1,
    input_duration: int = 0,
    web_search: bool = False,
    dry_run: bool = False,
):
    """创建视频生成任务。返回 task_id。"""
    import urllib.request
    model_id = resolve_model(model)

    # 构造 content
    content = [{"type": "text", "text": prompt}]
    if image_url:
        image_url = _normalize_visual_input(image_url)
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url},
            "role": image_role,
        })
    if last_frame_url:
        last_frame_url = _normalize_visual_input(last_frame_url)
        content.append({
            "type": "image_url",
            "image_url": {"url": last_frame_url},
            "role": "last_frame",
        })
    for ref in reference_images or []:
        ref = _normalize_visual_input(ref)
        content.append({
            "type": "image_url",
            "image_url": {"url": ref},
            "role": "reference_image",
        })
    for ref in reference_videos or []:
        ref = _normalize_remote_input(ref, kind="参考视频")
        content.append({
            "type": "video_url",
            "video_url": {"url": ref},
            "role": "reference_video",
        })
    for ref in reference_audios or []:
        ref = _normalize_remote_input(ref, kind="参考音频")
        content.append({
            "type": "audio_url",
            "audio_url": {"url": ref},
            "role": "reference_audio",
        })

    # 估算费用
    effective_input_duration = input_duration
    if (reference_videos or []) and effective_input_duration <= 0:
        print("⚠️ 检测到 reference_video，但未提供 --input-duration；费用估算会偏低", file=sys.stderr)
    cost_info = estimate_video_cost(
        model_id, resolution, ratio, duration,
        input_duration=effective_input_duration,
        has_audio=generate_audio,
        service_tier="online" if service_tier == "default" else "offline",
    )
    print(f"📋 模型: {model_id} | 预估: {cost_info['tokens']} tokens ≈ ¥{cost_info['yuan']:.2f} ({cost_info['note']})", file=sys.stderr)

    body = {
        "model": model_id,
        "content": content,
        "resolution": resolution,
        "ratio": ratio,
        "duration": duration,
        "generate_audio": generate_audio,
        "return_last_frame": return_last_frame,
        "service_tier": service_tier,
        "watermark": watermark,
    }
    if web_search:
        body["tools"] = [{"type": "web_search"}]
    if seed >= 0:
        body["seed"] = seed
    if dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return "dry-run"

    req = urllib.request.Request(
        "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
        data=json.dumps(body).encode(),
        headers=_video_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            task = json.loads(resp.read())
    except HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="ignore")
        except Exception:
            detail = ""
        msg = f"视频任务创建失败: HTTP {e.code} {e.reason}"
        if e.code == 401:
            msg += "。请检查 ARK_API_KEY 是否已设置且有效"
        if detail:
            msg += f"\n{detail}"
        raise RuntimeError(msg) from e

    task_id = task.get("id", "")
    print(f"🎬 任务已提交: {task_id}", file=sys.stderr)

    _print_summary(
        kind="video", model=model, model_id=model_id,
        cost=cost_info["yuan"], count=1,
        outputs=[task_id],
        extra={
            "resolution": resolution,
            "duration": duration,
            "ratio": ratio,
            "reference_videos": len(reference_videos or []),
            "reference_images": len(reference_images or []),
            "reference_audios": len(reference_audios or []),
        },
    )
    return task_id


def poll_task(task_id: str, interval: int = 10, timeout: int = 600):
    """轮询视频任务直到完成。返回最终状态。"""
    import urllib.request
    elapsed = 0
    while elapsed < timeout:
        url = f"https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}"
        req = urllib.request.Request(url, headers=_video_headers())
        with urllib.request.urlopen(req) as resp:
            task = json.loads(resp.read())
        status = task.get("status", "")
        if status in ("succeeded", "failed", "cancelled", "expired"):
            print(f"\n🏁 任务 {task_id}: {status}", file=sys.stderr)
            outputs = [task_id]
            content = task.get("content", {})
            if content:
                vurl = content.get("video_url", "")
                if vurl:
                    outdir = _default_output_dir()
                    vpath = os.path.join(outdir, f"ark_vid_{task_id}.mp4")
                    try:
                        _download_image(vurl, vpath)
                        print(f"  📹 视频: {vpath}", file=sys.stderr)
                        outputs.append(vpath)
                    except Exception as e:
                        print(f"  📹 视频: {vurl} (下载失败: {e})", file=sys.stderr)
                        outputs.append(vurl)
                lfu = content.get("last_frame_url", "")
                if lfu:
                    outdir = _default_output_dir()
                    lfpath = os.path.join(outdir, f"ark_last_frame_{task_id}.png")
                    try:
                        _download_image(lfu, lfpath)
                        print(f"  🖼️ 尾帧: {lfpath}", file=sys.stderr)
                        outputs.append(lfpath)
                    except Exception as e:
                        print(f"  🖼️ 尾帧: {lfu} (下载失败: {e})", file=sys.stderr)
                        outputs.append(lfu)
                usage = task.get("usage", {})
                tokens = usage.get("completion_tokens", 0)
                if tokens:
                    print(f"  📊 Tokens: {tokens}", file=sys.stderr)
            tmodel = task.get("model", "unknown")
            _print_summary(
                kind="video_result", model=tmodel, model_id=str(tmodel),
                cost=0, count=1, outputs=outputs,
                extra={"status": status, "tokens": tokens},
            )
            return task
        print(f"⏳ [{elapsed}s] 状态: {status}...", file=sys.stderr)
        time.sleep(interval)
        elapsed += interval
    print(f"⏰ 超时 ({timeout}s)", file=sys.stderr)
    return None


def list_tasks(status: Optional[str] = None, page_size: int = 10):
    """查询视频任务列表。"""
    import urllib.request
    url = f"https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks?page_size={page_size}"
    if status:
        url += f"&filter.status={status}"
    req = urllib.request.Request(url, headers=_video_headers())
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    print(f"共 {data.get('total', 0)} 个任务", file=sys.stderr)
    for item in data.get("items", []):
        s = item.get("status", "?")
        m = item.get("model", "?")
        d = item.get("duration", "?")
        tid = item.get("id", "?")
        tokens = item.get("usage", {}).get("completion_tokens", "?")
        video = item.get("content", {}).get("video_url", "")
        print(f"  {tid} | {m} | {s} | {d}s | tokens={tokens}")
        if video:
            print(f"    📹 {video}")
    return data


def cancel_task(task_id: str):
    """取消/删除任务。"""
    import urllib.request
    url = f"https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}"
    req = urllib.request.Request(url, method="DELETE", headers=_video_headers())
    with urllib.request.urlopen(req) as resp:
        print(f"✅ 任务 {task_id} 已取消/删除", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ark Media Helper")
    sub = parser.add_subparsers(dest="command")

    # generate-image
    p_img = sub.add_parser("generate-image", help="生成图像")
    p_img.add_argument("prompt")
    p_img.add_argument("--model", default="seedream-5.0")
    p_img.add_argument("--size", default="2K")
    p_img.add_argument("--image", help="单张参考图路径或URL")
    p_img.add_argument("--images", nargs="+", help="多张参考图路径或URL（多图融合/多图生组图）")
    p_img.add_argument("--format", default="png", dest="output_format")
    p_img.add_argument("--sequential", default="disabled", choices=["disabled", "auto"])
    p_img.add_argument("--max-images", type=int, default=4)
    p_img.add_argument("--stream", action="store_true")
    p_img.add_argument("--watermark", action="store_true")
    p_img.add_argument("--output-dir", default=None, help="输出目录（默认 ~/Downloads）")

    # generate-video
    p_vid = sub.add_parser("generate-video", help="创建视频生成任务")
    p_vid.add_argument("prompt")
    p_vid.add_argument("--model", default="seedance-2.0")
    p_vid.add_argument("--resolution", default="720p")
    p_vid.add_argument("--ratio", default="16:9")
    p_vid.add_argument("--duration", type=int, default=5)
    p_vid.add_argument("--image", help="首帧图片 URL")
    p_vid.add_argument("--image-role", default="first_frame")
    p_vid.add_argument("--last-frame", help="尾帧图片 URL")
    p_vid.add_argument("--reference-images", nargs="+", help="参考图片 URL / asset:// / 本地图片路径")
    p_vid.add_argument("--reference-videos", nargs="+", help="参考视频 URL / asset://（最多 3 个）")
    p_vid.add_argument("--reference-audios", nargs="+", help="参考音频 URL / asset://（最多 3 个）")
    p_vid.add_argument("--input-duration", type=int, default=0, help="参考视频总时长（秒），用于更准确费用估算")
    p_vid.add_argument("--audio", action="store_true", default=True)
    p_vid.add_argument("--no-audio", dest="audio", action="store_false")
    p_vid.add_argument("--return-last-frame", action="store_true")
    p_vid.add_argument("--offline", action="store_true")
    p_vid.add_argument("--seed", type=int, default=-1)
    p_vid.add_argument("--watermark", action="store_true")
    p_vid.add_argument("--web-search", action="store_true", help="启用 Seedance 2.0 web_search 工具（仅纯文本输入建议使用）")
    p_vid.add_argument("--dry-run", action="store_true", help="仅打印最终请求体，不提交任务")

    # poll
    p_poll = sub.add_parser("poll", help="轮询视频任务")
    p_poll.add_argument("task_id")
    p_poll.add_argument("--interval", type=int, default=10)
    p_poll.add_argument("--timeout", type=int, default=600)

    # cost
    p_cost = sub.add_parser("cost", help="估算费用")
    p_cost.add_argument("type", choices=["image", "video"])
    p_cost.add_argument("--model", required=True)
    p_cost.add_argument("--count", type=int, default=1, help="图片数量")
    p_cost.add_argument("--resolution", default="720p")
    p_cost.add_argument("--ratio", default="16:9")
    p_cost.add_argument("--duration", type=int, default=5)
    p_cost.add_argument("--input-duration", type=int, default=0, help="输入视频时长")
    p_cost.add_argument("--audio", action="store_true", default=True)
    p_cost.add_argument("--no-audio", dest="audio", action="store_false")
    p_cost.add_argument("--offline", action="store_true")

    # list-tasks
    p_list = sub.add_parser("list-tasks", help="查询任务列表")
    p_list.add_argument("--status", choices=["queued", "running", "succeeded", "failed", "cancelled", "expired"])
    p_list.add_argument("--page-size", type=int, default=10)

    # cancel
    p_cancel = sub.add_parser("cancel", help="取消/删除任务")
    p_cancel.add_argument("task_id")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "generate-image":
        urls = generate_image(
            prompt=args.prompt,
            model=args.model,
            size=args.size,
            image=args.image,
            images=getattr(args, 'images', None),
            output_format=args.output_format,
            sequential=args.sequential,
            max_images=args.max_images,
            watermark=args.watermark,
            stream=args.stream,
            output_dir=getattr(args, 'output_dir', None),
        )
        for url in urls:
            print(url)

    elif args.command == "generate-video":
        task_id = generate_video(
            prompt=args.prompt,
            model=args.model,
            resolution=args.resolution,
            ratio=args.ratio,
            duration=args.duration,
            image_url=args.image,
            image_role=args.image_role,
            last_frame_url=args.last_frame,
            reference_images=getattr(args, 'reference_images', None),
            reference_videos=getattr(args, 'reference_videos', None),
            reference_audios=getattr(args, 'reference_audios', None),
            generate_audio=args.audio,
            return_last_frame=args.return_last_frame,
            service_tier="flex" if args.offline else "default",
            watermark=args.watermark,
            seed=args.seed,
            input_duration=getattr(args, 'input_duration', 0),
            web_search=getattr(args, 'web_search', False),
            dry_run=getattr(args, 'dry_run', False),
        )
        print(task_id)

    elif args.command == "poll":
        poll_task(args.task_id, args.interval, args.timeout)

    elif args.command == "cost":
        model_id = resolve_model(args.model)
        if args.type == "image":
            cost = estimate_image_cost(model_id, args.count)
            print(f"图像: {model_id} × {args.count}张 = ¥{cost:.2f}")
        else:
            info = estimate_video_cost(
                model_id, args.resolution, args.ratio, args.duration,
                input_duration=args.input_duration,
                has_audio=args.audio,
                service_tier="offline" if args.offline else "online",
            )
            print(f"视频: {model_id} | {args.resolution} {args.ratio} {args.duration}s")
            print(f"  Tokens: {info['tokens']:,} | 费用: ¥{info['yuan']:.2f} | {info['note']}")

    elif args.command == "list-tasks":
        list_tasks(args.status, args.page_size)

    elif args.command == "cancel":
        cancel_task(args.task_id)


if __name__ == "__main__":
    main()
