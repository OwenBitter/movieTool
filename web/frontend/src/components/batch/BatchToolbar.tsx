import { Button, Space, Checkbox } from 'antd';
import { DeleteOutlined, FolderOutlined, CopyOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { useAppState } from '../../context/AppContext';
import { openFiltered } from '../../api';

interface BatchToolbarProps {
  totalCount: number;
  onBatch: (mode: 'delete' | 'move' | 'copy') => void;
}

export function BatchToolbar({ totalCount, onBatch }: BatchToolbarProps) {
  const { state, dispatch } = useAppState();
  const selectedCount = state.selected.size;

  if (selectedCount === 0) return null;

  const allSelected = selectedCount === totalCount;

  const toggleAll = () => {
    // In a real implementation, we'd need all movie IDs
    // For now, clear selection
    dispatch({ type: 'SET_SELECTED', ids: new Set() });
  };

  return (
    <div className="batch-toolbar">
      <Checkbox checked={allSelected} onChange={toggleAll}>
        已选 {selectedCount} 部
      </Checkbox>
      <Button size="small" onClick={() => dispatch({ type: 'SET_SELECTED', ids: new Set() })}>
        取消选择
      </Button>
      <Space style={{ marginLeft: 'auto' }}>
        <Button
          size="small"
          icon={<FolderOpenOutlined />}
          onClick={() => openFiltered([...state.selected])}
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
      </Space>
    </div>
  );
}
