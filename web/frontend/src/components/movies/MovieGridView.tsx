import { LoadingOutlined } from '@ant-design/icons';
import { Spin } from 'antd';
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
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spin indicator={<LoadingOutlined style={{ fontSize: 32, color: '#e8b84b' }} />} />
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
