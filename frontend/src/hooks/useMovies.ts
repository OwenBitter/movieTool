import { useEffect, useCallback, useState } from 'react';
import { useStore } from '../store';
import * as api from '../api';
import type { Movie } from '../types';

export function useMovies() {
  const movies = useStore((s) => s.movies);
  const setLoading = useStore((s) => s.setLoading);
  const [data, setData] = useState<Movie[]>([]);

  const loadMovies = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (movies.actor) params.actor = movies.actor;
      if (movies.tags.length > 0) params.tags = movies.tags.join(',');
      if (movies.rating > 0) params.rating = String(movies.rating);
      if (movies.status) params.status = movies.status;
      if (movies.search) params.search = movies.search;
      params.sort = movies.sort;

      const result = await api.fetchMovies(params);
      setData(result.movies);
    } catch (e) {
      console.error('Failed to load movies:', e);
    } finally {
      setLoading(false);
    }
  }, [movies, setLoading]);

  useEffect(() => {
    loadMovies();
  }, [loadMovies]);

  return { movies: data, reload: loadMovies };
}
