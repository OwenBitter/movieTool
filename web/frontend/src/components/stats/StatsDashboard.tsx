import { useState, useEffect } from 'react';
import { Modal, Card, Progress, Statistic, Row, Col, Table, Tag, Rate, Spin } from 'antd';
import {
  DatabaseOutlined, StarOutlined, TagsOutlined, ClockCircleOutlined,
  FolderOutlined, RiseOutlined,
} from '@ant-design/icons';
import type { StatsDetail } from '../../types';

interface StatsDashboardProps {
  open: boolean;
  onClose: () => void;
}

export function StatsDashboard({ open, onClose }: StatsDashboardProps) {
  const [data, setData] = useState<StatsDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && !data) {
      setLoading(true);
      fetch('/api/stats/detail')
        .then((r) => r.json())
        .then((d) => { setData(d); setLoading(false); })
        .catch(() => setLoading(false));
    }
  }, [open, data]);

  if (!data) {
    return (
      <Modal title="📊 统计面板" open={open} onCancel={onClose} footer={null} width={700}>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin />
        </div>
      </Modal>
    );
  }

  const maxTagCount = Math.max(...Object.values(data.tag_counts), 1);
  const maxRating = Math.max(...Object.values(data.rating_distribution), 1);

  return (
    <Modal
      title="📊 统计面板"
      open={open}
      onCancel={onClose}
      footer={null}
      width={720}
    >
      {/* Overview cards */}
      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        <Col span={8}>
          <Card size="small">
            <Statistic title="总影片" value={data.total} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic title="总大小" value={data.total_size} prefix={<FolderOutlined />} valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic title="平均评分" value={data.avg_rating} prefix={<StarOutlined />} suffix={`/5`} precision={1} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        <Col span={8}>
          <Card size="small">
            <Statistic title="已分类" value={data.classified} suffix={`/ ${data.total}`} />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic title="已评分" value={data.rated} suffix={`/ ${data.total}`} prefix={<StarOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic title="7日内新下载" value={data.recent_downloads} prefix={<RiseOutlined style={{ color: '#2ecc71' }} />} />
          </Card>
        </Col>
      </Row>

      {/* Rating distribution */}
      <Card title="⭐ 评分分布" size="small" style={{ marginBottom: 16 }}>
        {[5, 4, 3, 2, 1].map((star) => (
          <div key={star} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={{ width: 50, textAlign: 'right' }}>
              <Rate disabled value={star} style={{ fontSize: 12 }} />
            </span>
            <Progress
              percent={Math.round((data.rating_distribution[star] / maxRating) * 100)}
              size="small"
              style={{ flex: 1, margin: 0 }}
              strokeColor="#e8b84b"
              trailColor="rgba(255,255,255,0.05)"
              format={() => `${data.rating_distribution[star]} 部`}
            />
          </div>
        ))}
      </Card>

      {/* Tag distribution - top 15 */}
      <Card title="🏷 标签分布 (TOP 15)" size="small" style={{ marginBottom: 16 }}>
        {Object.entries(data.tag_counts).slice(0, 15).map(([tag, count]) => (
          <div key={tag} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <Tag color="default" style={{ minWidth: 48, textAlign: 'center' }}>{tag}</Tag>
            <Progress
              percent={Math.round((count / maxTagCount) * 100)}
              size="small"
              style={{ flex: 1, margin: 0 }}
              strokeColor="#3b82f6"
              trailColor="rgba(255,255,255,0.05)"
              format={() => `${count} 部`}
            />
          </div>
        ))}
      </Card>

      {/* Top 10 actors */}
      <Card title="🎭 演员 TOP 10" size="small">
        <Table
          dataSource={data.top_actors}
          rowKey="name"
          size="small"
          pagination={false}
          columns={[
            { title: '#', key: 'rank', width: 40, render: (_: unknown, __: unknown, i: number) => i + 1 },
            { title: '演员', dataIndex: 'name', key: 'name' },
            {
              title: '影片数',
              dataIndex: 'count',
              key: 'count',
              width: 80,
              render: (c: number) => (
                <Progress
                  percent={Math.round((c / (data.top_actors[0]?.count || 1)) * 100)}
                  size="small"
                  style={{ margin: 0, width: 70 }}
                  strokeColor="#e8b84b"
                  trailColor="rgba(255,255,255,0.05)"
                  format={() => c}
                />
              ),
            },
          ]}
        />
      </Card>
    </Modal>
  );
}
