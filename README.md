# ykt

雨课堂刷课脚本

1. 刷课
2. 完成作业
3. 自动讨论

## 快速开始

### 打包文件运行

开箱即用 已配置好题库请**合理使用**

1. 从最新 Releases 中下载 zip 压缩包
2. 解压运行`ykt.exe`即可

### 源码运行

本项目使用 uv 管理环境

1. clone 项目至本地
2. `cd ykt`
3. `uv sync`
4. `uv run main.py`

## 配置项

`config.toml`为配置文件

```toml
# 是否开启课程名称过滤 当课程过多时可开启此项 开启后只显示名称中包含当前年份的课程
isFilter = true
# 是否开启题目记录 开启后会向云端题库上传所有做过的题目的正确答案
isRecord = true
# 是否跳过答题 开启后只刷视频不答题
isSkipQuiz = false

[tiku]
# 题库链接
url = ""
```

## 打包命令

打包完成后需要手动拷贝 decode/table.json 和 cofig.toml 文件到 exe 同级目录下

```powershell
nuitka --mode=onefile --windows-icon-from-ico=logo.ico --mingw64 --jobs=8 --include-data-files=decode/table.json=decode/table.json  --include-package=websockets  --output-dir=output main.py
```
