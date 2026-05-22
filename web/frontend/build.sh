#!/bin/bash
cd /mnt/e/tools/movieTool/web/frontend
npx vite build --logLevel info 2>&1
echo "BUILD_EXIT:$?"
