# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python + Excel movie management system for scanning, classifying, tagging, and browsing Japanese AV video files. Three interfaces share the same `core/` modules: a CLI (`main.py`), a Tkinter GUI (`ui/`), and a Flask + React/TypeScript web app (`web/`).

## Commands

```bash
# CLI mode
python main.py --cli scan|classify|copy|backup|fetch|show
python main.py scan          # scan download_dir, write to Excel
python main.py classify      # move files into classify_dir by actor
python main.py copy          # copy managed files to copy_target_dir
python main.py backup        # backup Excel file
python main.py fetch --name "CODE-123"
python main.py show --status classified

# Web app (Flask backend + React frontend)
python web/app.py            # starts on http://localhost:5000

# React frontend dev
cd frontend && npm run dev    # Vite dev server
cd frontend && npm run build  # TypeScript + Vite production build → web/static/dist/
```

## Architecture

```
main.py              # CLI/GUI entry point, builds AppContext, dispatches commands
core/
  app_context.py     # Shared context: holds ConfigManager + Logger + ExcelManager, provides maybe_backup()
  config_manager.py  # JSON config read/write/validate/ensure_paths; auto-creates default config.json
  excel_manager.py   # OpenPyXL wrapper — Excel IS the database. Stores 11-column movie records.
  scanner.py         # Walks download_dir, discovers video files, adds/updates Excel rows
  classifier.py      # Moves files into classify_dir/<actor>/ folders, updates status=classified
  copier.py          # Copies managed files to copy_target_dir (dedup by file size)
  metadata_fetcher.py   # Queries external movie metadata API
  actress_fetcher.py    # Scrapes njavtv.art to extract actress names from AV codes
  logger.py          # Timestamped rotating log files with auto-cleanup
ui/
  main_window.py     # Tkinter GUI with tabs: config, tools, logs
web/
  app.py             # Flask API server (20+ endpoints) — serves React SPA + REST API, no DB
  static/dist/       # Built React SPA (served at /)
frontend/            # React 18 + TypeScript + AntD 5 + Zustand + Vite
```

**Excel as database**: `excel_manager.py` uses a Chinese header row for display but maps everything to English internal keys (`movie_id`, `file_name`, `movie_name`, `actor`, `release_year`, `rating`, `file_size`, `file_path`, `status`, `tags`, `downloaded_at`). Movie ID is `SHA1(file_path)[:12]`.

**WSL paths**: Config paths use `/mnt/e/...` (WSL mounted drive). `web/app.py` has `_wsl_to_win()` to convert to `E:\...` for Windows Explorer and PowerShell operations.

**Config sections**: `path_config`, `format_config`, `backup_config`, `log_config`, `api_config`, `tag_config`, `rating_config`.

**Tag system**: Two groups — `available_tags` (attribute tags like 中字, 巨乳) and `type_tags` (studio/series like S1, MOODYZ). Tags stored as comma-separated strings in Excel. Custom tags are auto-detected from usage.

**Backup**: When `backup_config.backup_frequency` is `every_operation`, scan/classify/copy auto-backup Excel via `AppContext.maybe_backup()`.

## Key details

- Excel is the sole persistent store — treat all Excel writes as data mutations.
- The React SPA build output goes to `web/static/dist/` (served by Flask at `/`).
- `requirements.txt`: openpyxl, requests, beautifulsoup4. Web app additionally needs `flask`.
- Actress scraping targets `https://www.njavtv.art/cn/{code}` and parses `女优: <name>` from HTML.
