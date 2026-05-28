"""
GIF 转换核心模块
compress_mode:
  none                  - 直接转换，不压缩
  keep_resolution       - 保持分辨率，降低帧率
  keep_fps              - 保持帧率，降低分辨率
  target_size           - 二分搜索，同时调整帧率+分辨率
  target_size_keep_res  - 二分搜索，仅调整帧率（保持分辨率）
  target_size_keep_fps  - 二分搜索，仅调整分辨率（保持帧率）
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Callable, Optional

from utils import FFMPEG, get_video_info, to_short_path, has_non_ascii


def _run(cmd: list) -> subprocess.CompletedProcess:
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    r = subprocess.run(cmd, capture_output=True, timeout=600, creationflags=flags)
    # 解码输出，兼容中文系统
    r.stdout = r.stdout.decode("utf-8", errors="replace") if isinstance(r.stdout, bytes) else r.stdout
    r.stderr = r.stderr.decode("utf-8", errors="replace") if isinstance(r.stderr, bytes) else r.stderr
    return r


class GifConverter:
    def __init__(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        self.cb = progress_callback or (lambda p, m: None)

    # ── Public entry ──────────────────────────────────────────────
    def convert(
        self,
        input_path: str,
        output_path: str,
        start_sec: float,
        end_sec: float,
        fps: int = 15,
        width: int = 480,
        height: int = -1,
        dither: str = "bayer",
        compress_mode: str = "none",
        target_size_mb: Optional[float] = None,
        **kwargs,
    ) -> str:
        duration = end_sec - start_sec
        if duration <= 0:
            raise ValueError("结束时间必须大于开始时间")

        # GIF 帧延迟精度为 0.01s，最高有效帧率 = 50fps
        fps = min(fps, 50)

        self.cb(3, "初始化...")

        # 从输入文件读取旋转信息（若调用方未传则自动检测）
        if "rotation" not in kwargs:
            info = get_video_info(input_path)
            kwargs["rotation"] = info.get("rotation", 0)

        kw = dict(input_path=input_path, output_path=output_path,
                  start_sec=start_sec, duration=duration,
                  fps=fps, width=width, height=height, dither=dither,
                  rotation=kwargs.get("rotation", 0))

        if compress_mode == "none":
            return self._once(**kw, ps=5, pe=95)
        elif compress_mode == "keep_resolution":
            return self._compress_keep_res(**kw)
        elif compress_mode == "keep_fps":
            return self._compress_keep_fps(**kw)
        elif compress_mode == "target_size":
            if target_size_mb is None:
                raise ValueError("需要指定目标文件大小")
            return self._target_size(**kw, target_mb=target_size_mb, mode="both")
        elif compress_mode == "target_size_keep_res":
            if target_size_mb is None:
                raise ValueError("需要指定目标文件大小")
            return self._target_size(**kw, target_mb=target_size_mb, mode="keep_res")
        elif compress_mode == "target_size_keep_fps":
            if target_size_mb is None:
                raise ValueError("需要指定目标文件大小")
            return self._target_size(**kw, target_mb=target_size_mb, mode="keep_fps")
        else:
            raise ValueError(f"未知压缩模式: {compress_mode}")

    # ── Core convert (one pass) ───────────────────────────────────
    def _once(self, input_path, output_path, start_sec, duration,
              fps, width, height, dither, rotation=0, ps=5, pe=95) -> str:

        # 中文路径处理：输入转短路径；输出含中文则先写临时文件
        safe_input = to_short_path(input_path)
        use_tmp_out = has_non_ascii(output_path)
        if use_tmp_out:
            tmp_out = tempfile.mktemp(suffix=".gif")
        else:
            tmp_out = output_path

        # 旋转 filter（手机竖拍视频有 rotate 元数据）
        # -noautorotate 禁用 ffmpeg 自动旋转，由我们显式控制方向
        # rotate=90  → 视频顺时针存储，需逆时针90°纠正 → transpose=2
        # rotate=270 → 视频逆时针存储，需顺时针90°纠正 → transpose=1
        if rotation == 90:
            rotate_f = "transpose=2,"    # 逆时针 90°
        elif rotation == 270:
            rotate_f = "transpose=1,"    # 顺时针 90°
        elif rotation == 180:
            rotate_f = "transpose=1,transpose=1,"  # 180°
        else:
            rotate_f = ""

        with tempfile.TemporaryDirectory() as tmp:
            palette = os.path.join(tmp, "pal.png")
            scale = self._scale(width, height)

            # Step 1: palette
            pf = f"{rotate_f}{scale},fps={fps},palettegen=stats_mode=diff"
            r = _run([FFMPEG, "-y", "-noautorotate",
                      "-ss", str(start_sec), "-t", str(duration),
                      "-i", safe_input, "-vf", pf, palette])
            if r.returncode != 0:
                raise RuntimeError(f"调色板生成失败: {r.stderr[-600:]}")
            self.cb(ps + int((pe - ps) * 0.35), "生成调色板完成，渲染 GIF...")

            # Step 2: render
            dopt = f":dither={dither}" if dither != "none" else ""
            gf = f"{rotate_f}{scale},fps={fps} [x]; [x][1:v] paletteuse=diff_mode=rectangle{dopt}"
            r = _run([FFMPEG, "-y", "-noautorotate",
                      "-ss", str(start_sec), "-t", str(duration),
                      "-i", safe_input, "-i", palette,
                      "-lavfi", gf, tmp_out])
            if r.returncode != 0:
                if use_tmp_out and os.path.exists(tmp_out):
                    os.unlink(tmp_out)
                raise RuntimeError(f"GIF 渲染失败: {r.stderr[-600:]}")

        # 输出路径含中文：移动到目标位置
        if use_tmp_out:
            shutil.move(tmp_out, output_path)

        self.cb(pe, "转换完成")
        return output_path

    # ── Keep resolution: reduce fps ──────────────────────────────
    def _compress_keep_res(self, input_path, output_path, start_sec, duration,
                           fps, width, height, dither, rotation=0) -> str:
        self.cb(8, "保持分辨率模式：生成基准 GIF...")
        self._once(input_path, output_path, start_sec, duration,
                   fps, width, height, dither, rotation=rotation, ps=8, pe=55)
        base_size = os.path.getsize(output_path)
        self.cb(58, f"基准: {base_size/1024/1024:.2f} MB，尝试降帧率...")

        for ratio in [0.67, 0.5, 0.33, 0.25]:
            nfps = max(1, int(fps * ratio))
            self.cb(int(58 + ratio * 35), f"尝试 {nfps} fps...")
            tmp = tempfile.mktemp(suffix=".gif")
            try:
                self._once(input_path, tmp, start_sec, duration,
                           nfps, width, height, dither, rotation=rotation, ps=0, pe=0)
                ns = os.path.getsize(tmp)
                if ns < base_size * 0.85:
                    shutil.move(tmp, output_path)
                    self.cb(95, f"压缩完成: {nfps} fps, {ns/1024/1024:.2f} MB")
                    return output_path
                else:
                    os.unlink(tmp)
            except Exception:
                if os.path.exists(tmp): os.unlink(tmp)

        self.cb(95, "完成（帧率已为最低）")
        return output_path

    # ── Keep fps: reduce resolution ──────────────────────────────
    def _compress_keep_fps(self, input_path, output_path, start_sec, duration,
                           fps, width, height, dither, rotation=0) -> str:
        self.cb(8, "保持帧率模式：生成基准 GIF...")
        self._once(input_path, output_path, start_sec, duration,
                   fps, width, height, dither, rotation=rotation, ps=8, pe=50)
        base_size = os.path.getsize(output_path)
        self.cb(53, f"基准: {base_size/1024/1024:.2f} MB，尝试降分辨率...")

        for ratio in [0.75, 0.6, 0.5, 0.4, 0.3]:
            nw = max(2, int(width * ratio))
            nw = nw - (nw % 2)
            nh = max(2, int(height * ratio)) if height > 0 else -1
            if nh > 0: nh = nh - (nh % 2)
            self.cb(int(53 + ratio * 40), f"尝试 {nw}px...")
            tmp = tempfile.mktemp(suffix=".gif")
            try:
                self._once(input_path, tmp, start_sec, duration,
                           fps, nw, nh, dither, rotation=rotation, ps=0, pe=0)
                ns = os.path.getsize(tmp)
                if ns < base_size * 0.85:
                    shutil.move(tmp, output_path)
                    self.cb(95, f"压缩完成: {nw}px, {ns/1024/1024:.2f} MB")
                    return output_path
                else:
                    os.unlink(tmp)
            except Exception:
                if os.path.exists(tmp): os.unlink(tmp)

        self.cb(95, "完成（分辨率已为最低）")
        return output_path

    # ── Target size (binary search) ──────────────────────────────
    def _target_size(self, input_path, output_path, start_sec, duration,
                     fps, width, height, dither, target_mb, mode="both", rotation=0) -> str:
        target_bytes = target_mb * 1024 * 1024
        self.cb(5, f"目标大小: {target_mb:.1f} MB，生成基准...")

        # baseline
        tmp_base = tempfile.mktemp(suffix=".gif")
        try:
            self._once(input_path, tmp_base, start_sec, duration,
                       fps, width, height, dither, rotation=rotation, ps=5, pe=28)
            base_size = os.path.getsize(tmp_base)
        finally:
            if os.path.exists(tmp_base): os.unlink(tmp_base)

        self.cb(30, f"基准: {base_size/1024/1024:.2f} MB，目标: {target_mb:.1f} MB")

        if base_size <= target_bytes * 1.05:
            self._once(input_path, output_path, start_sec, duration,
                       fps, width, height, dither, rotation=rotation, ps=30, pe=95)
            return output_path

        # binary search
        lo, hi = 0.1, 1.0
        best_tmp = None
        best_size = float("inf")

        for i in range(9):
            mid = (lo + hi) / 2

            if mode == "keep_res":
                # only reduce fps
                trial_fps = max(1, int(fps * mid))
                trial_w = width
                trial_h = height
            elif mode == "keep_fps":
                # only reduce resolution
                trial_fps = fps
                trial_w = max(2, int(width * mid))
                trial_w -= trial_w % 2
                trial_h = max(2, int(height * mid)) if height > 0 else -1
                if trial_h > 0: trial_h -= trial_h % 2
            else:
                # adjust both
                trial_fps = max(1, int(fps * mid))
                trial_w = max(2, int(width * mid))
                trial_w -= trial_w % 2
                trial_h = max(2, int(height * mid)) if height > 0 else -1
                if trial_h > 0: trial_h -= trial_h % 2

            pct = int(30 + i * 7)
            label = f"迭代{i+1}/9"
            if mode == "keep_res":
                self.cb(pct, f"{label}: fps={trial_fps}...")
            elif mode == "keep_fps":
                self.cb(pct, f"{label}: w={trial_w}px...")
            else:
                self.cb(pct, f"{label}: fps={trial_fps}, w={trial_w}px...")

            tmp = tempfile.mktemp(suffix=".gif")
            try:
                self._once(input_path, tmp, start_sec, duration,
                           trial_fps, trial_w, trial_h, dither, rotation=rotation, ps=0, pe=0)
                ts = os.path.getsize(tmp)
                if ts <= target_bytes:
                    if best_tmp and os.path.exists(best_tmp):
                        os.unlink(best_tmp)
                    best_tmp = tmp
                    best_size = ts
                    lo = mid
                else:
                    os.unlink(tmp)
                    hi = mid
                if abs(ts - target_bytes) / target_bytes < 0.04:
                    break
            except Exception:
                if os.path.exists(tmp): os.unlink(tmp)
                hi = mid

        if best_tmp and os.path.exists(best_tmp):
            shutil.move(best_tmp, output_path)
            self.cb(95, f"目标压缩完成: {best_size/1024/1024:.2f} MB")
        else:
            self.cb(88, "未能达到目标，使用最小参数...")
            mfps = max(1, fps // 4)
            mw = max(2, width // 4)
            mw -= mw % 2
            mh = max(2, height // 4) - (max(2, height // 4) % 2) if height > 0 else -1
            self._once(input_path, output_path, start_sec, duration,
                       mfps, mw, mh, dither, rotation=rotation, ps=88, pe=95)

        return output_path

    # ── Helpers ───────────────────────────────────────────────────
    @staticmethod
    def _scale(width: int, height: int = -1) -> str:
        if height > 0:
            return f"scale={width}:{height}:flags=lanczos"
        return f"scale={width}:-2:flags=lanczos"
