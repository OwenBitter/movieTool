import { Rate, message } from 'antd';
import { updateMovie } from '../../api';

interface StarRatingProps {
  movieId: string;
  rating: number;
  onUpdated: () => void;
}

export function StarRating({ movieId, rating, onUpdated }: StarRatingProps) {
  const handleChange = async (value: number) => {
    try {
      await updateMovie(movieId, { rating: value });
      message.success('评分已保存');
      onUpdated();
    } catch (e) {
      message.error('评分保存失败');
    }
  };

  return <Rate value={rating} onChange={handleChange} />;
}
