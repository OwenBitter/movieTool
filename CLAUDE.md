# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Python + Excel movie management system for scanning, classifying, tagging, and browsing JAV files. Flask backend split into `web/routes/`, React 18 + TypeScript + Ant Design 5 + Zustand frontend at `frontend/`.

## Quick Commands

```bash
# Web UI (production)
cd /mnt/e/tools/movieTool && PYTHONPATH=/mnt/e/tools/movieTool python3 web/app.py  # → :5000

# Frontend
cd frontend && npx vite build              # production build → web/static/dist/
cd frontend && npx tsc --noEmit            # type check

# CLI
python3 main.py scan|classify|copy|backup|show

# Data enrichment
python3 scripts/enrich_from_javbus.py --apply       # javbus: dates + tags + covers
python3 scripts/tag_by_code.py --apply               # code prefix → type tags
python3 scripts/tag_actresses.py                     # actress → attribute tags
python3 scripts/pregen_thumbs.py --generate          # ffmpeg thumbnails
python3 scripts/detect_dupes.py                      # duplicate detection
```

## Architecture (v4.2)

```
core/
├── excel_manager.py     # 11-column Excel CRUD
├── config_manager.py    # JSON config (paths, tags, rating)
├── javbus_fetcher.py    # javbus.com search/detail/cover
├── scanner.py           # Discover new files → Excel
├── classifier.py        # Move files by actor
├── copier.py            # Copy to external drives
├── tag_utils.py         # merge_tags()
├── logger.py            # Timestamped rotating logs
├── app_context.py       # Shared ctx: Config + Logger + Excel
web/
├── app.py               # Flask init + SPA fallback (~45 lines)
├── shared.py            # _load_config, get_excel, filter_records, format_movie...
├── server_state.py      # In-memory cache (actors, tags_usage, stats) — invalidate() on mutations
├── watcher.py           # watchdog file monitor (auto-add new files)
├── routes/
│   ├── movies.py        # /api/movies GET/PATCH, quick-rate, export
│   ├── actors.py        # /api/actors, /api/actress/<name>/detail
│   ├── tags.py          # /api/tags CRUD
│   ├── batch.py         # batch delete/move/copy/tags
│   ├── stats.py         # /api/stats, /api/stats/detail
│   ├── files.py         # open-folder, open-filtered, play, thumb, cover
│   ├── backups.py       # backup list/create/restore/delete
│   ├── metadata.py      # POST /api/metadata/scan
│   └── progress.py      # SSE /api/progress/<task_id>
frontend/
├── src/
│   ├── store/index.ts   # Zustand store + async fetch actions
│   ├── hooks/           # Thin selectors (useMovies, useTags, useActors, useRating, useUndo)
│   ├── components/      # movies/, tags/, batch/, stats/, layout/, actress/, backup/, rating/
│   ├── types.ts, api.ts, App.tsx, App.css
│   └── styles/theme.ts  # Cinema Noir dark theme
├── vite.config.ts       # outDir: ../web/static/dist, proxy /api → :5000
└── package.json         # react 18, antd 5, zustand 5, typescript 5, vite 6
scripts/
├── enrich_from_javbus.py  # Batch javbus: dates + translated tags + covers
├── tag_by_code.py         # JAV prefix → type tags (80+ mappings)
├── tag_actresses.py       # Actress → attribute tags (144 KB)
├── pregen_thumbs.py       # Batch ffmpeg thumbnails
└── detect_dupes.py        # Duplicate code detection
```

## Key Conventions

- **WSL paths**: always `/mnt/e/...`, never `E:\...`
- **python3** not python on WSL
- **Proxy**: `export https_proxy=http://172.24.144.1:7890`
- **Excel**: 11 columns, tags as comma-separated string (never array in API)
- **Excel save**: batch modify rows directly, call `save()` once. Never `update_movie()` in a loop.
- **Classify**: only when actor field is non-empty
- **ServerState cache**: all mutations MUST call `get_state().invalidate()`
- **Frontend build on WSL**: `cd frontend && npx vite build`. If EIO errors, use `npm install` not rm.
- **Cover API**: `/api/cover/<movie_id>` — extracts JAV code from movie_name, serves from `cover_dir`
- **javbus cookies**: stored in `javbus_cookies.json` at project root

## Data Sources

| Source | Access | Data |
|--------|--------|------|
| javbus.com | Proxy + cookies | Actress, tags, release_date, cover, studio |
| javdb.com | Proxy | Actress, date |

## Config

`config.json` paths: `download_dir`, `classify_dir`, `backup_dir` (`/mnt/e/tools/movieTool/backups`), `cover_dir` (`/mnt/e/tools/movieTool/covers`).
Tags: `available_tags` (attribute), `type_tags` (category), `allow_custom`, `delimiter`.

## Pitfalls

1. WSL `rm -rf node_modules` fails with EIO on /mnt/ → use `npm install` to reinstall
2. `npx vite build` may be rejected as "server process" → use `background=true`
3. Cover images need `Referer` header from detail page URL
4. javbus requires age-verify POST + driver quiz (one-time, cookies exported from browser)
5. Tag manager: delete no confirm, dialog stays open, no auto-close
6. Store `fetchMovies` in Zustand — don't duplicate fetch logic in hooks
