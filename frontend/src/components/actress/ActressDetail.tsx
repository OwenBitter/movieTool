import { useEffect, useState } from 'react';
import { Drawer, Tag, Card, Statistic, Row, Col, Progress, List, Typography, Spin } from 'antd';
import { StarOutlined, FolderOutlined, DatabaseOutlined, PlayCircleOutlined } from '@ant-design/icons';
import type { Movie } from '../../types';
import { useStore } from '../../store';

interface ActressData {
  name: string;
  total: number;
  rated: number;
  avg_rating: number;
  total_size: string;
  rating_distribution: Record<number, number>;
  top_tags: Record<string, number>;
  movies: Movie[];
}

interface Props {
  name: string | null;
  onClose: () => void;
}

export function ActressDetail({ name, onClose }: Props) {
  const toggleTag = useStore((s) => s.toggleTag);
  const [data, setData] = useState<ActressData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!name) { setData(null); return; }
    setLoading(true);
    fetch(`/api/actress/${encodeURIComponent(name)}/detail`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [name]);

  const handleMovieClick = (movieId: string) => {
    fetch(`/api/play/${movieId}`, { method: 'POST' }).catch(() => {});
  };

  const maxTagCount = data ? Math.max(1, ...Object.values(data.top_tags)) : 1;

  return (
    <Drawer
      title={name ? `${name} · 详情` : ''}
      open={name !== null}
      onClose={onClose}
      width={420}
      styles={{ body: { padding: '16px 20px' } }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
      ) : data ? (
        <>
          {/* Stats */}
          <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card size="small">
                <Statistic title="作品数" value={data.total} prefix={<DatabaseOutlined />} />
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small">
                <Statistic title="总大小" value={data.total_size} prefix={<FolderOutlined />} valueStyle={{ fontSize: 18 }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small">
                <Statistic title="平均评分" value={data.avg_rating} prefix={<StarOutlined />} precision={1} suffix={`/ 5`} />
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small">
                <Statistic title="已评分" value={`${data.rated} / ${data.total}`} />
              </Card>
            </Col>
          </Row>

          {/* Rating distribution */}
          <Card title="⭐ 评分分布" size="small" style={{ marginBottom: 12 }}>
            {[5, 4, 3, 2, 1].map((star) => (
              <div key={star} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ width: 20, textAlign: 'right', color: '#e8b84b' }}>{star}</span>
                <Progress
                  percent={data.total > 0 ? Math.round((data.rating_distribution[star] || 0) / data.total * 100) : 0}
                  size="small"
                  showInfo={false}
                  strokeColor="#e8b84b"
                  trailColor="rgba(255,255,255,0.05)"
                  style={{ flex: 1 }}
                />
                <span style={{ width: 24, fontSize: 12, color: '#88889a' }}>{data.rating_distribution[star] || 0}</span>
              </div>
            ))}
          </Card>

          {/* Top tags */}
          <Card title="🏷️ 常用标签" size="small" style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {Object.entries(data.top_tags).map(([tag, count]) => (
                <Tag
                  key={tag}
                  color="default"
                  style={{ cursor: 'pointer', opacity: Math.max(0.5, count / maxTagCount) }}
                  onClick={() => toggleTag(tag)}
                >
                  {tag} ({count})
                </Tag>
              ))}
              {Object.keys(data.top_tags).length === 0 && (
                <Typography.Text type="secondary">暂无标签</Typography.Text>
              )}
            </div>
          </Card>

          {/* Movie list */}
          <Card title={`📼 作品列表 (${data.total})`} size="small">
            <List
              size="small"
              dataSource={data.movies}
              renderItem={(m) => (
                <List.Item
                  style={{ cursor: 'pointer', padding: '6px 0' }}
                  onClick={() => handleMovieClick(m.movie_id)}
                >
                  <div style={{ flex: 1 }}>
                    <span style={{ color: '#e8b84b', fontWeight: 600, fontSize: 13 }}>{m.movie_name || m.file_name}</span>
                    <div style={{ fontSize: 12, color: '#88889a' }}>
                      <StarOutlined style={{ marginRight: 2 }} />{m.rating || '-'} · {m.file_size} · {m.downloaded_at?.slice(0, 10) || '-'}
                    </div>
                  </div>
                  <PlayCircleOutlined style={{ color: '#3b82f6', fontSize: 16 }} />
                </List.Item>
              )}
            />
          </Card>
        </>
      ) : null}
    </Drawer>
  );
}
