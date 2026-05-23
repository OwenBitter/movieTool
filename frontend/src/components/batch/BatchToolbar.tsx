import { Button, Space, Checkbox } from 'antd';
import { DeleteOutlined, FolderOutlined, CopyOutlined, FolderOpenOutlined, TagsOutlined } from '@ant-design/icons';
import { useStore } from '../../store';
import { openFiltered } from '../../api';
import type { Movie } from '../../types';

interface BatchToolbarProps {
  movies: Movie[];
  onBatch: (mode: 'delete' | 'move' | 'copy' | 'tags') => void;
}

export function BatchToolbar({ movies, onBatch }: BatchToolbarProps) {
  const selected = useStore((s) => s.selected);
  const setSelected = useStore((s) => s.setSelected);
  const selectedCount = selected.size;
  const totalCount = movies.length;

  if (selectedCount === 0) return null;

  const allSelected = totalCount > 0 && selectedCount >= totalCount;

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(movies.map((m) => m.movie_id)));
    }
  };

  return (
    <div className="batch-toolbar">
      <Checkbox checked={allSelected} onChange={toggleAll}>
        已选 {selectedCount} 部
      </Checkbox>
      <Button size="small" onClick={() => setSelected(new Set())}>
        取消选择
      </Button>
      <Space style={{ marginLeft: 'auto' }}>
        <Button
          size="small"
          icon={<FolderOpenOutlined />}
          onClick={() => openFiltered([...selected])}
        >
          打开所在目录
        </Button>
        <Button size="small" icon={<DeleteOutlined />} danger onClick={() => onBatch('delete')}>
          删除
        </Button>
        <Button size="small" icon={<FolderOutlined />} onClick={() => onBatch('move')}>
          移动
        </Button>
        <Button size="small" icon={<CopyOutlined />} onClick={() => onBatch('copy')}>
          复制
        </Button>
        <Button size="small" icon={<TagsOutlined />} onClick={() => onBatch('tags')}>
          标签
        </Button>
      </Space>
    </div>
  );
}
