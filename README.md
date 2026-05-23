# 电影自动化管理系统

基于 Python + Excel + React 的电影文件扫描、分类、标签管理和浏览工具。

## 架构

```
core/           # 核心模块 (Excel CRUD, 扫描, 分类, 复制等)
web/            # Flask 后端 + React 前端静态文件
  app.py          # Flask 入口
  routes/         # API 路由
  shared.py       # 共享工具
  server_state.py # 缓存
  static/dist/    # 前端构建产物
frontend/       # React 18 + Ant Design 5 + Zustand 前端
scripts/        # 数据增强脚本 (javbus, 标签, 缩略图)
```

## 启动

### Flask 后端 (Windows)

```bash
cd /d E:\tools\movieTool
set PYTHONPATH=E:\tools\movieTool
set PYTHONIOENCODING=utf-8
python web\app.py
```

访问 `http://localhost:5000`

### 重启 Flask

若修改了 `web/` 下的 Python 文件，需要先终止旧进程再重新启动：

```bash
# 终止端口 5000 的进程
powershell -Command "Stop-Process -Id (Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue).OwningProcess -Force"

# 重新启动
cd /d E:\tools\movieTool
set PYTHONPATH=E:\tools\movieTool
set PYTHONIOENCODING=utf-8
python web\app.py
```

### 前端开发模式

```bash
cd /d E:\tools\movieTool\frontend
npx vite
```
默认 `http://localhost:5173`，API 代理到 Flask `:5000`。

### 前端构建

```bash
cd /d E:\tools\movieTool\frontend
npx vite build
```
产物输出到 `web/static/dist/`，由 Flask 直接 serve。

## 命令

```bash
python main.py scan          # 扫描下载目录，更新 Excel
python main.py classify       # 根据演员分类移动文件
python main.py copy           # 复制到外部硬盘
python main.py backup         # 备份 Excel
python main.py show           # 显示影片列表
python scripts/enrich_from_javbus.py --apply   # 从 javbus 获取日期/标签/封面
python scripts/pregen_thumbs.py --generate     # 批量生成缩略图
python scripts/tag_by_code.py --apply          # 按番号前缀打标签
```

## 依赖

```bash
pip install flask openpyxl requests watchdog
cd frontend && npm install
```
