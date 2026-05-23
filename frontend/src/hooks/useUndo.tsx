import { useRef, useCallback } from 'react';
import { message } from 'antd';
import { updateMovie } from '../api';

interface UndoEntry {
  movieId: string;
  field: 'rating' | 'tags';
  oldValue: string | number;
  timestamp: number;
}

interface BatchUndoEntry {
  movieIds: string[];
  field: 'rating' | 'tags';
  oldValues: Map<string, string | number>;
  timestamp: number;
}

const MAX_HISTORY = 30;
const UNDO_TIMEOUT = 3000;

export function useUndo(onReload: () => void) {
  const history = useRef<UndoEntry[]>([]);
  const batchHistory = useRef<BatchUndoEntry[]>([]);

  const push = useCallback((movieId: string, field: 'rating' | 'tags', oldValue: string | number) => {
    history.current.push({ movieId, field, oldValue, timestamp: Date.now() });
    if (history.current.length > MAX_HISTORY) {
      history.current.shift();
    }
  }, []);

  const pushBatch = useCallback((movieIds: string[], field: 'tags', oldValues: Map<string, string | number>) => {
    batchHistory.current.push({ movieIds, field, oldValues, timestamp: Date.now() });
    if (batchHistory.current.length > MAX_HISTORY) {
      batchHistory.current.shift();
    }
  }, []);

  const undo = useCallback(async (entry: UndoEntry) => {
    try {
      if (entry.field === 'rating') {
        await updateMovie(entry.movieId, { rating: Number(entry.oldValue) });
      } else {
        await updateMovie(entry.movieId, { tags: String(entry.oldValue) });
      }
      message.success('已撤销');
      onReload();
    } catch {
      message.error('撤销失败');
    }
  }, [onReload]);

  const undoBatch = useCallback(async (entry: BatchUndoEntry) => {
    try {
      const promises = entry.movieIds.map((id) => {
        const oldVal = entry.oldValues.get(id);
        if (oldVal !== undefined) {
          return updateMovie(id, { tags: String(oldVal) });
        }
        return Promise.resolve();
      });
      await Promise.all(promises);
      message.success('已批量撤销');
      onReload();
    } catch {
      message.error('批量撤销失败');
    }
  }, [onReload]);

  const showUndoMessage = useCallback((
    movieOrIds: string | string[],
    field: 'rating' | 'tags',
    oldValue: string | number | Map<string, string | number>,
  ) => {
    const msgKey = `undo-${Date.now()}`;

    if (Array.isArray(movieOrIds)) {
      const entry: BatchUndoEntry = {
        movieIds: movieOrIds,
        field: field as 'tags',
        oldValues: oldValue as Map<string, string | number>,
        timestamp: Date.now(),
      };
      pushBatch(entry.movieIds, 'tags', entry.oldValues);

      message.success({
        content: (
          <span>
            已批量保存{' '}
            <a
              onClick={() => {
                undoBatch(entry);
                message.destroy(msgKey);
              }}
              style={{ color: '#e8b84b', fontWeight: 600 }}
            >
              ↩ 撤销
            </a>
          </span>
        ),
        key: msgKey,
        duration: UNDO_TIMEOUT / 1000,
      });
    } else {
      const entry: UndoEntry = {
        movieId: movieOrIds,
        field,
        oldValue: oldValue as string | number,
        timestamp: Date.now(),
      };
      push(entry.movieId, entry.field, entry.oldValue);

      message.success({
        content: (
          <span>
            已保存{' '}
            <a
              onClick={() => {
                undo(entry);
                message.destroy(msgKey);
              }}
              style={{ color: '#e8b84b', fontWeight: 600 }}
            >
              ↩ 撤销
            </a>
          </span>
        ),
        key: msgKey,
        duration: UNDO_TIMEOUT / 1000,
      });
    }
  }, [push, pushBatch, undo, undoBatch]);

  return { showUndoMessage };
}
