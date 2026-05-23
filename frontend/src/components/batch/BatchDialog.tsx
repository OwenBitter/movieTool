import { Modal, Input, Button, Space, Tag, Typography, message } from 'antd';
import { DeleteOutlined, FolderOutlined, CopyOutlined } from '@ant-design/icons';
import { useState, useEffect } from 'react';
import { deleteMovies, moveMovies, copyMovies, batchSetTags } from '../../api';

interface BatchDialogProps {
  open: boolean;
  mode: 'delete' | 'move' | 'copy' | 'tags' | null;
  count: number;
  selectedIds: string[];
  onClose: () => void;
  onDone: () => void;
}

export function BatchDialog({ open, mode, count, selectedIds, onClose, onDone }: BatchDialogProps) {
  const [dest, setDest] = useState('');
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState<Record<string, string[]>>({});

  useEffect(() => {
    if (open && mode === 'tags') {
      fetch('/api/tag-templates')
        .then((r) => r.json())
        .then(setTemplates)
        .catch(() => {});
    }
  }, [open, mode]);

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
      } else if (mode === 'tags') {
        await batchSetTags(selectedIds, dest.split(',').map((t) => t.trim()).filter(Boolean));
        message.success(`已应用标签到 ${count} 部影片`);
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

  const handleApplyTemplate = (tags: string[]) => {
    setDest(tags.join(','));
  };

  const titles: Record<string, string> = {
    delete: '确认删除',
    move: '移动影片',
    copy: '复制影片',
    tags: '批量标签',
  };
  const icons: Record<string, React.ReactNode> = {
    delete: <DeleteOutlined style={{ color: '#c0392b' }} />,
    move: <FolderOutlined />,
    copy: <CopyOutlined />,
    tags: null,
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
          : mode === 'tags'
          ? `已选择 ${count} 部影片，将替换所有标签`
          : `已选择 ${count} 部影片`}
      </p>

      {mode === 'tags' && (
        <>
          {Object.keys(templates).length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                标签模板（点击快速填入）:
              </Typography.Text>
              <Space wrap size={[4, 4]}>
                {Object.entries(templates).map(([name, tags]) => (
                  <Tag
                    key={name}
                    style={{ cursor: 'pointer' }}
                    color="blue"
                    onClick={() => handleApplyTemplate(tags)}
                  >
                    {name}
                  </Tag>
                ))}
              </Space>
            </div>
          )}
          <Input
            placeholder="输入标签，逗号分隔，如 高清,中字,推荐"
            value={dest}
            onChange={(e) => setDest(e.target.value)}
          />
        </>
      )}

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
