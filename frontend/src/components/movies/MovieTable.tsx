import { Table, Tag, Rate, Space, Tooltip } from 'antd';
import { FolderOpenOutlined, PlayCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Movie } from '../../types';
import { useStore } from '../../store';
import { openFolder, playMovie } from '../../api';
import { useRating } from '../../hooks/useRating';

interface MovieTableProps {
  movies: Movie[];
  onUpdated: () => void;
}

export function MovieTable({ movies, onUpdated }: MovieTableProps) {
  const selected = useStore((s) => s.selected);
  const loading = useStore((s) => s.loading);
  const setSelected = useStore((s) => s.setSelected);
  const { handleRatingChange } = useRating({ onUpdated });

  const rowSelection = {
    selectedRowKeys: [...selected],
    onChange: (keys: React.Key[]) => {
      setSelected(new Set(keys as string[]));
    },
  };

  const columns: ColumnsType<Movie> = [
    {
      title: '番号',
      dataIndex: 'movie_name',
      key: 'movie_name',
      width: 140,
      render: (text: string, record: Movie) => (
        <Space>
          <Tooltip title="播放">
            <PlayCircleOutlined
              style={{ color: '#3b82f6', cursor: 'pointer' }}
              onClick={() => playMovie(record.movie_id)}
            />
          </Tooltip>
          <span style={{ color: '#e8b84b', fontWeight: 600 }}>{text || record.file_name}</span>
        </Space>
      ),
    },
    {
      title: '演员',
      dataIndex: 'actor',
      key: 'actor',
      width: 110,
      render: (text: string) => text || '—',
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      width: 160,
      render: (value: number, record: Movie) => (
        <Rate value={value} onChange={(v) => handleRatingChange(record.movie_id, v)} style={{ fontSize: 14 }} />
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (text: string) => {
        if (!text) return null;
        return (
          <Space size={[2, 2]} wrap>
            {text.split(',').filter(Boolean).map((t) => (
              <Tag key={t} color="default">{t.trim()}</Tag>
            ))}
          </Space>
        );
      },
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 90,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (s: string) => (s === 'classified' ? '已分类' : '未分类'),
    },
    {
      title: '下载时间',
      dataIndex: 'downloaded_at',
      key: 'downloaded_at',
      width: 110,
      render: (text: string) => (text ? text.slice(0, 10) : '—'),
    },
    {
      title: '',
      key: 'actions',
      width: 50,
      render: (_: unknown, record: Movie) => (
        <Tooltip title="资源管理器">
          <FolderOpenOutlined
            style={{ color: '#88889a', cursor: 'pointer' }}
            onClick={() => openFolder(record.movie_id)}
          />
        </Tooltip>
      ),
    },
  ];

  return (
    <Table
      rowKey="movie_id"
      columns={columns}
      dataSource={movies}
      rowSelection={rowSelection}
      size="middle"
      loading={loading}
      pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (t) => `共 ${t} 部` }}
      scroll={{ x: 900 }}
      style={{ padding: '0 20px' }}
    />
  );
}
