import { Modal, Input, Button, Space, message } from 'antd';
import { DeleteOutlined, FolderOutlined, CopyOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { deleteMovies, moveMovies, copyMovies } from '../../api';

interface BatchDialogProps {
  open: boolean;
  mode: 'delete' | 'move' | 'copy' | null;
  count: number;
  selectedIds: string[];
  onClose: () => void;
  onDone: () => void;
}

export function BatchDialog({ open, mode, count, selectedIds, onClose, onDone }: BatchDialogProps) {
  const [dest, setDest] = useState('');
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      if (mode === 'delete') {
        await deleteMovies(selectedIds);
        message.success(`已删除 ${count} 部影片`);
      } else if (mode === 'move') {
        if (!dest.trim()) { message.warning('请输入目标路径'); setLoading(false); return; }
        await moveMovies(selectedIds, dest);
        message.success(`已移动 ${count} 部影片`);
      } else if (mode === 'copy') {
        if (!dest.trim()) { message.warning('请输入目标路径'); setLoading(false); return; }
        await copyMovies(selectedIds, dest);
        message.success(`已复制 ${count} 部影片`);
      }
      onDone();
      onClose();
    } catch (e) {
      message.error('操作失败');
    } finally {
      setLoading(false);
    }
  };

  if (!mode) return null;

  const titles: Record<string, string> = {
    delete: '确认删除',
    move: '移动影片',
    copy: '复制影片',
  };
  const icons: Record<string, React.ReactNode> = {
    delete: <DeleteOutlined style={{ color: '#c0392b' }} />,
    move: <FolderOutlined />,
    copy: <CopyOutlined />,
  };

  return (
    <Modal
      title={<span>{icons[mode]} {titles[mode]}</span>}
      open={open}
      onCancel={onClose}
      footer={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button type={mode === 'delete' ? 'primary' : 'primary'} danger={mode === 'delete'} loading={loading} onClick={handleConfirm}>
            确认
          </Button>
        </Space>
      }
    >
      <p style={{ marginBottom: 12 }}>
        {mode === 'delete'
          ? `确定要删除 ${count} 部影片吗？此操作不可逆！`
          : `已选择 ${count} 部影片`}
      </p>
      {(mode === 'move' || mode === 'copy') && (
        <Input
          placeholder="输入目标路径，如 /mnt/e/目标目录"
          value={dest}
          onChange={(e) => setDest(e.target.value)}
        />
      )}
    </Modal>
  );
}
