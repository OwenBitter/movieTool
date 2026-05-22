# 电影自动化管理系统

一个基于 Python + Excel 的电影文件扫描、分类、复制和备份管理工具。

## 目录结构

- `config.json` - 系统配置文件
- `requirements.txt` - Python 依赖
- `main.py` - 命令行入口
- `core/` - 核心模块
  - `config_manager.py`
  - `logger.py`
  - `excel_manager.py`
  - `scanner.py`
  - `classifier.py`
  - `copier.py`
  - `metadata_fetcher.py`
- `ui/` - GUI 占位模块

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方式

进入 `movieTool` 目录后执行：

```bash
python main.py
```

或双击 `start.bat`，即可打开图形界面。

如果你希望使用命令行模式，可以加上 `--cli`：

```bash
python main.py --cli
python main.py --cli scan
python main.py --cli classify
```

也可以直接运行命令：

```bash
python main.py init
python main.py scan
python main.py classify
python main.py copy
python main.py backup
python main.py fetch --name "影片名称或代码"
python main.py show
```

## 说明

- `scan`：扫描 `config.json` 中配置的 `download_dir`，并自动写入或更新 Excel 文件。
- `classify`：根据演员或文件名分类并移动视频文件到 `classify_dir`。
- `copy`：将当前已管理的视频文件复制到 `copy_target_dir`。
- `backup`：备份当前 Excel 文件到 `backup_dir`。
- `fetch`：调用配置中的元数据 API 查询影片信息。
- `女优查询`：从下载目录提取 AV 代码并查询女优信息，结果写入 Excel。

## 配置

可以直接在图形界面里编辑配置：

- `download_dir`
- `classify_dir`
- `excel_path`
- `copy_target_dir`
- `backup_dir`

在界面中修改后点击“保存配置”，系统会写回 `config.json` 并生效。

如果你希望手动编辑 `config.json`，也可以这样做，然后运行 `python main.py init` 生成 Excel 文件。
