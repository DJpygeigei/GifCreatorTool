import os
import sys
import subprocess
import json
import re
from pathlib import Path


def to_short_path(path: str) -> str:
    """
    Windows 上将含中文的路径转换为 8.3 短路径，供 subprocess 使用。
    非 Windows 或转换失败时原路返回。路径必须已存在。
    """
    if os.name != "nt":
        return path
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        ret = ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 1024)
        if ret > 0:
            return buf.value
    except Exception:
        pass
    return path


def has_non_ascii(path: str) -> bool:
    """检查路径是否包含非 ASCII 字符（中文等）"""
    try:
        path.encode("ascii")
        return False
    except UnicodeEncodeError:
        return True


def _find_ffmpeg():
    """查找ffmpeg可执行文件：优先项目内bundled，其次PATH"""
    # 打包后 ffmpeg 放在同级目录
    base_dir = Path(__file__).parent
    for name in ("ffmpeg.exe", "ffmpeg"):
        bundled = base_dir / name
        if bundled.exists():
            return str(bundled)
    return "ffmpeg"


def _find_ffprobe():
    base_dir = Path(__file__).parent
    for name in ("ffprobe.exe", "ffprobe"):
        bundled = base_dir / name
        if bundled.exists():
            return str(bundled)
    return "ffprobe"


FFMPEG = _find_ffmpeg()
FFPROBE = _find_ffprobe()


def get_video_info(path: str) -> dict:
    """用 ffprobe 获取视频基础信息"""
    try:
        safe_path = to_short_path(path)
        cmd = [
            FFPROBE, "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            safe_path
        ]
        result = subprocess.run(
            cmd, capture_output=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        data = json.loads(result.stdout.decode("utf-8", errors="replace"))

        info = {}
        # Duration from format
        fmt = data.get("format", {})
        info["duration"] = float(fmt.get("duration", 0))

        # Video stream
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                info["width"] = stream.get("width", 0)
                info["height"] = stream.get("height", 0)
                # FPS
                fps_str = stream.get("r_frame_rate", "25/1")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    info["fps"] = float(num) / float(den) if float(den) != 0 else 25.0
                else:
                    info["fps"] = float(fps_str)

                # ── 旋转元数据检测 ──
                # 方式1：tags 里的 rotate
                rotation = 0
                tags = stream.get("tags", {})
                if "rotate" in tags:
                    rotation = abs(int(tags["rotate"]))
                # 方式2：side_data_list 里的 Display Matrix
                for sd in stream.get("side_data_list", []):
                    if sd.get("side_data_type") == "Display Matrix":
                        r = sd.get("rotation", 0)
                        if r:
                            rotation = abs(int(r))
                        break
                info["rotation"] = rotation
                # 90/270度旋转时，实际显示宽高需要交换
                if rotation in (90, 270):
                    info["width"], info["height"] = info["height"], info["width"]
                break
        return info
    except Exception as e:
        return {}


def format_time(seconds: float) -> str:
    """秒 → MM:SS.mmm"""
    if seconds < 0:
        seconds = 0
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m:02d}:{s:06.3f}"


def parse_time(time_str: str) -> float:
    """MM:SS.mmm → 秒"""
    try:
        if ":" in time_str:
            parts = time_str.split(":")
            m = int(parts[0])
            s = float(parts[1])
            return m * 60 + s
        return float(time_str)
    except Exception:
        return 0.0


def resource_path(filename: str) -> str:
    """获取资源文件绝对路径，兼容开发环境和 PyInstaller 打包"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def estimate_gif_bytes(duration_sec: float, fps: int, width: int, height: int,
                       compress_mode: str, target_mb: float = None) -> int:
    """
    粗略估算 GIF 文件大小（字节）。
    GIF 用 8-bit 调色板 + LZW 压缩，典型压缩率约 0.45。
    """
    if duration_sec <= 0 or fps <= 0 or width <= 0 or height <= 0:
        return 0

    # 指定目标大小模式：直接返回目标值
    if compress_mode in ("target_size", "target_size_keep_res", "target_size_keep_fps"):
        if target_mb and target_mb > 0:
            return int(target_mb * 1024 * 1024)

    frames = duration_sec * fps
    w, h = float(width), float(height)

    # 根据压缩模式调整估算参数
    if compress_mode == "keep_resolution":
        frames *= 0.5       # 保持分辨率模式：帧率降约 50%
    elif compress_mode == "keep_fps":
        w *= 0.6            # 保持帧率模式：分辨率降约 60%
        h *= 0.6

    # LZW 压缩因子：典型视频内容约 0.45
    compression_factor = 0.45
    estimated = frames * w * h * compression_factor
    return max(0, int(estimated))


def format_size(size_bytes: int) -> str:
    """字节数 → 人类可读大小字符串"""
    if size_bytes <= 0:
        return "--"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"
