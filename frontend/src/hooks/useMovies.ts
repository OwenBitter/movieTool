import { useEffect, useCallback } from 'react';
import { useStore } from '../store';

export function useMovies() {
  const movieList = useStore((s) => s.movieList);
  const fetchMovies = useStore((s) => s.fetchMovies);
  const filters = useStore((s) => s.movies);

  // Re-fetch whenever filters change
  useEffect(() => {
    fetchMovies();
  }, [filters, fetchMovies]);

  const reload = useCallback(() => {
    fetchMovies();
  }, [fetchMovies]);

  return { movies: movieList, reload };
}
