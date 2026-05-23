import { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Space, Progress, Typography, Tag, App, Tooltip } from 'antd';
import { StarFilled, StarOutlined, PlayCircleOutlined, RightOutlined, ForwardOutlined } from '@ant-design/icons';
import type { Movie } from '../../types';

const BASE = '/api';

async function fetchUnrated(): Promise<{ movie: Movie | null; rated: number; total: number; done: boolean }> {
  const resp = await fetch(`${BASE}/movies/quick-rate`);
  if (!resp.ok) throw new Error('Failed to fetch');
  return resp.json();
}

async function rateMovie(id: string, rating: number): Promise<void> {
  await fetch(`${BASE}/movies/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rating }),
  });
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function QuickRate({ open, onClose }: Props) {
  const [movie, setMovie] = useState<Movie | null>(null);
  const [rated, setRated] = useState(0);
  const [total, setTotal] = useState(0);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const { message } = App.useApp();

  const loadNext = useCallback(async () => {
    setRating(null);
    setLoading(true);
    try {
      const data = await fetchUnrated();
      setMovie(data.movie);
      setRated(data.rated);
      setTotal(data.total);
      setDone(data.done);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    if (open) {
      setDone(false);
      setRated(0);
      setTotal(0);
      loadNext();
    }
  }, [open, loadNext]);

  const handleRate = async (value: number) => {
    if (!movie || loading) return;
    setRating(value);
    setLoading(true);
    try {
      await rateMovie(movie.movie_id, value);
      message.success(`${movie.movie_name || movie.file_name} — ${value} 星`);
      loadNext();
    } catch {
      message.error('评分失败');
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (!loading) loadNext();
  };

  // Keyboard shortcuts
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const key = e.key;
      if (key >= '1' && key <= '5') {
        handleRate(Number(key));
      } else if (key.toLowerCase() === 's') {
        handleSkip();
      } else if (key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, movie, loading]); // eslint-disable-line react-hooks/exhaustive-deps

  const pct = total > 0 ? Math.round((rated / total) * 100) : 0;

  return (
    <Modal
      title="⚡ 快速评分"
      open={open}
      onCancel={onClose}
      footer={null}
      width={520}
      destroyOnClose
    >
      {/* Progress */}
      <div style={{ marginBottom: 16 }}>
        <Progress percent={pct} size="small" />
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          已评分 {rated} / {total}（{pct}%）
        </Typography.Text>
      </div>

      {done ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Typography.Title level={4} style={{ color: '#2ecc71' }}>
            全部评分完毕！
          </Typography.Title>
          <Typography.Text type="secondary">
            共 {total} 部影片全部已评分
          </Typography.Text>
        </div>
      ) : movie ? (
        <div style={{ textAlign: 'center' }}>
          {/* Movie info */}
          <Typography.Title level={5} style={{ color: '#e8b84b', marginBottom: 4 }}>
            {movie.movie_name || movie.file_name}
          </Typography.Title>
          <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
            {movie.actor || '未知演员'} · {movie.file_size}
          </Typography.Text>
          {movie.tags && (
            <div style={{ marginBottom: 12 }}>
              {movie.tags.split(',').filter(Boolean).map((t) => (
                <Tag key={t} color="default">{t.trim()}</Tag>
              ))}
            </div>
          )}

          {/* Star rating buttons */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 36, letterSpacing: 8, marginBottom: 8 }}>
              {[1, 2, 3, 4, 5].map((star) => (
                <Tooltip key={star} title={`${star} 星`}>
                  <span
                    onClick={() => handleRate(star)}
                    style={{
                      cursor: loading ? 'not-allowed' : 'pointer',
                      color: rating === star ? '#e8b84b' : '#555',
                      opacity: loading ? 0.5 : 1,
                      transition: 'color 0.15s',
                    }}
                    onMouseEnter={(e) => {
                      if (!loading) (e.target as HTMLElement).style.color = '#e8b84b';
                    }}
                    onMouseLeave={(e) => {
                      if (!loading) (e.target as HTMLElement).style.color = '#555';
                    }}
                  >
                    {star <= (rating || 0) ? <StarFilled /> : <StarOutlined />}
                  </span>
                </Tooltip>
              ))}
            </div>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              键盘 1-5 打分 · S 跳过 · Esc 关闭
            </Typography.Text>
          </div>

          {/* Actions */}
          <Space>
            <Button
              icon={<ForwardOutlined />}
              onClick={handleSkip}
              disabled={loading}
            >
              跳过
            </Button>
          </Space>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Typography.Text type="secondary">加载中...</Typography.Text>
        </div>
      )}
    </Modal>
  );
}
