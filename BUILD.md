# GIFTool 打包流程

---

## 一、本地打包（Windows EXE）

### 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.11.x |
| PySide6 | ≥ 6.5.0 |
| PyInstaller | ≥ 6.0 |
| Pillow | ≥ 10.0 |
| mss | ≥ 9.0 |
| ffmpeg.exe / ffprobe.exe | 放在项目根目录 |

本机 Python 路径（已确认可用）：
```
C:\Users\wupengyu1\Desktop\wuzucatProject\.cowork-temp\wuzu_downloader_9xjbzv4k\python\3.11.8\unzip\platform-windows\arch-AMD64\Scripts\pyinstaller.exe
```

### 打包命令

```bat
cd C:\Users\wupengyu1\Desktop\giftool

"C:\Users\wupengyu1\Desktop\wuzucatProject\.cowork-temp\wuzu_downloader_9xjbzv4k\python\3.11.8\unzip\platform-windows\arch-AMD64\Scripts\pyinstaller.exe" giftool.spec --noconfirm
```

输出文件：`dist\GIFTool.exe`

### 发布前检查清单

- [ ] 更新 `main.py` 中的 `VERSION = "x.x.x"`
- [ ] 确认 `ffmpeg.exe` 和 `ffprobe.exe` 在项目根目录
- [ ] 确认 `docs/user_guide.html` 内容最新
- [ ] 打包完成后运行 `dist\GIFTool.exe` 验证版本号显示正确

---

## 二、GitHub Actions 打包（Windows EXE + macOS App）

### 触发条件

推送带 `v` 前缀的 tag 即自动触发，同时构建 Windows 和 macOS 版本：

```bat
cd C:\Users\wupengyu1\Desktop\giftool

git add .
git commit -m "描述本次改动"
git tag v1.x.x
git push origin master
git push origin v1.x.x
```

> **注意**：tag 名称必须与 `VERSION` 字段对应，CI 会自动将 main.py 里的 VERSION 替换为 tag 版本号。

### CI 自动完成的事

1. 安装 Python 3.11 + 依赖（PySide6 / PyInstaller / Pillow / mss）
2. 下载 ffmpeg（Windows 从 gyan.dev，macOS 用 brew）
3. 将 `VERSION = "x.x.x"` 替换为当前 tag 的版本号
4. 运行 `pyinstaller giftool.spec --noconfirm`
5. macOS 额外打包成 `GIFTool-macOS.zip`
6. 自动创建 GitHub Release，上传两个产物

### 查看构建结果

- Actions 页面：https://github.com/DJpygeigei/GifCreatorTool/actions
- Releases 页面：https://github.com/DJpygeigei/GifCreatorTool/releases

构建约需 **10 分钟**。

---

## 三、版本号管理规则

| 场景 | 操作 |
|------|------|
| 本地调试/测试打包 | 手动改 `main.py` 中 `VERSION` |
| 发布 GitHub Release | 推 tag，CI 自动注入，无需手动改 |
| 本地版本与 tag 对齐 | 发完 tag 再手动把 `main.py` 改成对应版本号 |

版本号格式：`主版本.次版本.修订号`（如 `1.1.2`）

---

## 四、常见问题

**Q：本地 `python` / `pyinstaller` 命令找不到？**  
A：直接用完整路径调用上方的 pyinstaller.exe，无需配置 PATH。

**Q：打包后运行报 `python311.dll` 错误？**  
A：自动更新脚本的重命名/替换逻辑问题，已在 v1.1.0 用 retry 循环修复，正常情况不再出现。

**Q：GitHub 下载的 EXE 版本号不对？**  
A：确认推 tag 前 `main.py` 中 VERSION 已更新，CI 替换的是已有 `VERSION = "..."` 字段。

**Q：macOS 版打开弹终端窗口？**  
A：需下载 `GIFTool-macOS.zip` 中的 `.app` 包版本（v1.0.5 起修复），不要用裸二进制。
