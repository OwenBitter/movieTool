import { useState } from 'react';
import { Modal, Table, Input, Button, Select, Space, Tag, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useStore } from '../../store';
import { addTag, renameTag, deleteTag, fetchTags } from '../../api';

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

export function TagManager({ open, onClose }: TagManagerProps) {
  const tagsConfig = useStore((s) => s.tagsConfig);
  const setTagsConfig = useStore((s) => s.setTagsConfig);
  const [newName, setNewName] = useState('');
  const [newGroup, setNewGroup] = useState('type');
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const tagConfig = tagsConfig;
  if (!tagConfig) return null;

  const allTags = [
    ...tagConfig.available_tags.map((t) => ({ name: t, group: 'attribute' as const })),
    ...tagConfig.type_tags.map((t) => ({ name: t, group: 'type' as const })),
    ...(tagConfig.custom_tags || []).map((t) => ({ name: t, group: 'custom' as const })),
  ];

  const usage = tagConfig.usage || {};

  const refresh = async () => {
    try {
      const config = await fetchTags();
      setTagsConfig(config);
    } catch (e) {
      console.error('Failed to reload tags:', e);
    }
  };

  const handleAdd = async () => {
    const name = newName.trim();
    if (!name) return;
    if (allTags.some((t) => t.name === name)) {
      message.warning('标签已存在');
      return;
    }
    try {
      await addTag(name, newGroup);
      message.success('标签已添加');
      setNewName('');
      await refresh();
    } catch (e) {
      message.error('添加失败');
    }
  };

  const handleRename = async (oldName: string) => {
    const nn = editValue.trim();
    if (!nn || nn === oldName) {
      setEditingTag(null);
      return;
    }
    try {
      await renameTag(oldName, nn);
      message.success('已重命名');
      setEditingTag(null);
      await refresh();
    } catch (e) {
      message.error('重命名失败');
    }
  };

  const handleDelete = async (name: string) => {
    try {
      await deleteTag(name);
      message.success('已删除');
      await refresh();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const groupLabel = (g: string) => {
    switch (g) {
      case 'attribute': return '属性';
      case 'type': return '类型';
      default: return '自定义';
    }
  };

  return (
    <Modal
      title="🏷 标签管理"
      open={open}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      {/* Add new tag */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <Select
          value={newGroup}
          onChange={setNewGroup}
          style={{ width: 100 }}
          options={[
            { value: 'attribute', label: '属性标签' },
            { value: 'type', label: '类型标签' },
          ]}
        />
        <Input
          placeholder="新标签名称"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onPressEnter={handleAdd}
        />
        <Button icon={<PlusOutlined />} onClick={handleAdd}>
          添加
        </Button>
      </div>

      {/* Tag list */}
      <Table
        rowKey="name"
        dataSource={allTags}
        pagination={false}
        size="small"
        columns={[
          {
            title: '标签',
            dataIndex: 'name',
            key: 'name',
            render: (name: string) => {
              if (editingTag === name) {
                return (
                  <Input
                    size="small"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onPressEnter={() => handleRename(name)}
                    onBlur={() => handleRename(name)}
                    autoFocus
                    style={{ width: 140 }}
                  />
                );
              }
              return <Tag color={name.startsWith('t:') ? 'blue' : 'default'}>{name}</Tag>;
            },
          },
          {
            title: '分组',
            dataIndex: 'group',
            key: 'group',
            width: 80,
            render: (g: string) => groupLabel(g),
          },
          {
            title: '使用',
            key: 'usage',
            width: 60,
            render: (_: unknown, r: { name: string }) => usage[r.name] || 0,
          },
          {
            title: '操作',
            key: 'actions',
            width: 100,
            render: (_: unknown, r: { name: string }) => (
              <Space>
                <Button
                  size="small"
                  type="text"
                  icon={<EditOutlined />}
                  onClick={() => {
                    setEditingTag(r.name);
                    setEditValue(r.name);
                  }}
                />
                <Button
                  size="small"
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(r.name)}
                />
              </Space>
            ),
          },
        ]}
      />
    </Modal>
  );
}
