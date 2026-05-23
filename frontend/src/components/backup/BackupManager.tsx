import { useEffect, useState } from 'react';
import { Modal, Button, Space, List, Typography, Popconfirm, App } from 'antd';
import { DeleteOutlined, RollbackOutlined, PlusOutlined, FolderOpenOutlined } from '@ant-design/icons';

interface BackupEntry {
  name: string;
  size: string;
  mtime: number;
  mtime_str: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function BackupManager({ open, onClose }: Props) {
  const [backups, setBackups] = useState<BackupEntry[]>([]);
  const [dir, setDir] = useState('');
  const [loading, setLoading] = useState(false);
  const { message } = App.useApp();

  const load = async () => {
    try {
      const resp = await fetch('/api/backups');
      const data = await resp.json();
      setBackups(data.backups);
      setDir(data.dir);
    } catch {
      message.error('加载备份列表失败');
    }
  };

  useEffect(() => {
    if (open) load();
  }, [open]);

  const create = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/backup/create', { method: 'POST' });
      const data = await resp.json();
      if (data.success) { message.success('备份已创建'); load(); }
      else message.error(data.error || '备份失败');
    } catch {
      message.error('备份失败');
    } finally {
      setLoading(false);
    }
  };

  const restore = async (filename: string) => {
    try {
      const resp = await fetch(`/api/backup/restore/${encodeURIComponent(filename)}`, { method: 'POST' });
      const data = await resp.json();
      if (data.success) message.success(`已从 ${filename} 恢复`);
      else message.error(data.error || '恢复失败');
    } catch {
      message.error('恢复失败');
    }
  };

  const remove = async (filename: string) => {
    try {
      const resp = await fetch(`/api/backup/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      const data = await resp.json();
      if (data.success) { message.success('已删除'); load(); }
      else message.error(data.error || '删除失败');
    } catch {
      message.error('删除失败');
    }
  };

  return (
    <Modal
      title="📦 备份管理"
      open={open}
      onCancel={onClose}
      width={560}
      footer={null}
      destroyOnClose
    >
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {dir || '未配置备份目录'}
        </Typography.Text>
        <Button icon={<PlusOutlined />} onClick={create} loading={loading} type="primary" size="small">
          立即备份
        </Button>
      </div>

      <List
        size="small"
        dataSource={backups}
        locale={{ emptyText: '暂无备份文件' }}
        renderItem={(b) => (
          <List.Item
            actions={[
              <Popconfirm key="restore" title="确认从此备份恢复？当前数据将被覆盖" onConfirm={() => restore(b.name)}>
                <Button size="small" icon={<RollbackOutlined />} type="link">恢复</Button>
              </Popconfirm>,
              <Popconfirm key="del" title="确认删除此备份？" onConfirm={() => remove(b.name)}>
                <Button size="small" icon={<DeleteOutlined />} type="link" danger>删除</Button>
              </Popconfirm>,
            ]}
          >
            <List.Item.Meta
              title={<span style={{ fontSize: 13 }}>{b.name}</span>}
              description={
                <span style={{ fontSize: 12, color: '#88889a' }}>
                  {b.size} · {b.mtime_str}
                </span>
              }
            />
          </List.Item>
        )}
      />
    </Modal>
  );
}
