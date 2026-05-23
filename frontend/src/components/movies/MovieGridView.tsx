import { Skeleton } from 'antd';
import type { Movie } from '../../types';
import { MovieCard } from './MovieCard';
import { useStore } from '../../store';

interface MovieGridViewProps {
  movies: Movie[];
  onUpdated: () => void;
}

export function MovieGridView({ movies, onUpdated }: MovieGridViewProps) {
  const loading = useStore((s) => s.loading);

  if (loading) {
    return (
      <div className="movie-grid">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="movie-card" style={{ padding: 16 }}>
            <Skeleton active paragraph={{ rows: 2 }} title={{ width: '60%' }} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="movie-grid">
      {movies.map((m) => (
        <MovieCard key={m.movie_id} movie={m} onUpdated={onUpdated} />
      ))}
    </div>
  );
}
