import { useRef, useCallback } from 'react';
import { message } from 'antd';
import { updateMovie } from '../api';

interface UndoEntry {
  movieId: string;
  field: 'rating' | 'tags';
  oldValue: string | number;
  timestamp: number;
}

const MAX_HISTORY = 30;
const UNDO_TIMEOUT = 3000; // 3 seconds

export function useUndo(onReload: () => void) {
  const history = useRef<UndoEntry[]>([]);

  const push = useCallback((movieId: string, field: 'rating' | 'tags', oldValue: string | number) => {
    history.current.push({ movieId, field, oldValue, timestamp: Date.now() });
    if (history.current.length > MAX_HISTORY) {
      history.current.shift();
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
    } catch (e) {
      message.error('撤销失败');
    }
  }, [onReload]);

  const showUndoMessage = useCallback((movieId: string, field: 'rating' | 'tags', oldValue: string | number) => {
    const entry: UndoEntry = { movieId, field, oldValue, timestamp: Date.now() };
    push(movieId, field, oldValue);

    const msgKey = `undo-${Date.now()}`;

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
  }, [push, undo]);

  return { showUndoMessage };
}
