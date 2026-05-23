import React, { useEffect, useCallback, useState } from 'react';
import { useAppState } from '../context/AppContext';
import * as api from '../api';
import type { Movie } from '../types';

export function useMovies() {
  const { state, dispatch } = useAppState();
  const [movies, setMovies] = useState<Movie[]>([]);

  const loadMovies = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const params: Record<string, string> = {};
      if (state.movies.actor) params.actor = state.movies.actor;
      if (state.movies.tags.length > 0) params.tags = state.movies.tags.join(',');
      if (state.movies.rating > 0) params.rating = String(state.movies.rating);
      if (state.movies.status) params.status = state.movies.status;
      if (state.movies.search) params.search = state.movies.search;
      params.sort = state.movies.sort;

      const data = await api.fetchMovies(params);
      setMovies(data.movies);
    } catch (e) {
      console.error('Failed to load movies:', e);
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  }, [state.movies, dispatch]);

  useEffect(() => {
    loadMovies();
  }, [loadMovies]);

  return { movies, reload: loadMovies };
}
