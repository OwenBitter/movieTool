import { useState, useMemo } from 'react';
import { Modal, Table, Input, Button, Select, Space, Tag, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useStore } from '../../store';
import { addTag, renameTag, deleteTag } from '../../api';

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
}

interface TagRow {
  name: string;
  group: 'attribute' | 'type' | 'custom';
}

const GROUP_COLORS: Record<TagRow['group'], string> = {
  attribute: 'blue',
  type: 'gold',
  custom: 'default',
};

const GROUP_LABEL: Record<TagRow['group'], string> = {
  attribute: '属性',
  type: '类型',
  custom: '自定义',
};

export function TagManager({ open, onClose }: TagManagerProps) {
  const tagsConfig = useStore((s) => s.tagsConfig);
  const fetchTags = useStore((s) => s.fetchTags);
  const [newName, setNewName] = useState('');
  const [newGroup, setNewGroup] = useState('type');
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [search, setSearch] = useState('');

  const tagConfig = tagsConfig;
  const usage = tagConfig?.usage || {};

  // Build sorted, filtered tag list
  const allTags = useMemo(() => {
    if (!tagConfig) return [];
    const rows: TagRow[] = [
      ...tagConfig.available_tags.map((t) => ({ name: t, group: 'attribute' as const })),
      ...tagConfig.type_tags.map((t) => ({ name: t, group: 'type' as const })),
      ...(tagConfig.custom_tags || []).map((t) => ({ name: t, group: 'custom' as const })),
    ];

    // Filter by search
    const filtered = search.trim()
      ? rows.filter((r) => r.name.toLowerCase().includes(search.toLowerCase()))
      : rows;

    // Sort: custom sort order by group, then by usage desc
    const groupOrder = { attribute: 0, type: 1, custom: 2 };
    return filtered.sort((a, b) => {
      // Show group header-level ordering
      const ga = groupOrder[a.group];
      const gb = groupOrder[b.group];
      if (ga !== gb) return ga - gb;
      // Within group: sort by usage desc
      const ua = usage[a.name] || 0;
      const ub = usage[b.name] || 0;
      return ub - ua;
    });
  }, [tagConfig, search, usage]);

  if (!tagConfig) return null;

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
      await fetchTags();
    } catch {
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
      await fetchTags();
    } catch {
      message.error('重命名失败');
    }
  };

  const handleDelete = async (name: string) => {
    try {
      await deleteTag(name);
      message.success('已删除');
      await fetchTags();
    } catch {
      message.error('删除失败');
    }
  };

  return (
    <Modal
      title={`🏷 标签管理 (${allTags.length})`}
      open={open}
      onCancel={onClose}
      footer={null}
      width={640}
    >
      {/* Add new tag */}
      <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
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

      {/* Search */}
      <div style={{ marginBottom: 12 }}>
        <Input.Search
          placeholder="搜索标签..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
      </div>

      {/* Tag list */}
      <Table<TagRow>
        rowKey="name"
        dataSource={allTags}
        pagination={false}
        size="small"
        scroll={{ y: 400 }}
        columns={[
          {
            title: '标签',
            dataIndex: 'name',
            key: 'name',
            render: (name: string, r: TagRow) => {
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
              return <Tag color={GROUP_COLORS[r.group]}>{name}</Tag>;
            },
          },
          {
            title: '分组',
            dataIndex: 'group',
            key: 'group',
            width: 70,
            render: (g: TagRow['group']) => (
              <span style={{ color: '#88889a', fontSize: 12 }}>{GROUP_LABEL[g]}</span>
            ),
          },
          {
            title: '使用',
            key: 'usage',
            width: 60,
            align: 'center',
            render: (_: unknown, r: TagRow) => {
              const count = usage[r.name] || 0;
              return (
                <span style={{ color: count > 0 ? '#e8b84b' : '#555', fontWeight: count > 0 ? 600 : 400 }}>
                  {count}
                </span>
              );
            },
          },
          {
            title: '操作',
            key: 'actions',
            width: 90,
            render: (_: unknown, r: TagRow) => (
              <Space size={0}>
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
