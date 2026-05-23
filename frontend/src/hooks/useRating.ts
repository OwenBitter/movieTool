import { useState, useCallback } from 'react';
import { message } from 'antd';
import { updateMovie } from '../api';

interface UseRatingOptions {
  onUpdated: () => void;
}

export function useRating({ onUpdated }: UseRatingOptions) {
  const [saving, setSaving] = useState(false);

  const handleRatingChange = useCallback(
    async (movieId: string, rating: number) => {
      setSaving(true);
      try {
        await updateMovie(movieId, { rating });
        message.success('评分已保存');
        onUpdated();
      } catch {
        message.error('评分保存失败');
      } finally {
        setSaving(false);
      }
    },
    [onUpdated],
  );

  return { saving, handleRatingChange };
}
