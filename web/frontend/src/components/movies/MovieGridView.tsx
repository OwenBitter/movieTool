import { Skeleton } from 'antd';
import type { Movie } from '../../types';
import { MovieCard } from './MovieCard';
import { useAppState } from '../../context/AppContext';

interface MovieGridViewProps {
  movies: Movie[];
  onUpdated: () => void;
}

export function MovieGridView({ movies, onUpdated }: MovieGridViewProps) {
  const { state } = useAppState();

  if (state.loading) {
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
        <div key={m.movie_id} className="movie-card-wrapper" style={{ contentVisibility: 'auto', containIntrinsicSize: 'auto 280px' }}>
          <MovieCard movie={m} onUpdated={onUpdated} />
        </div>
      ))}
    </div>
  );
}
