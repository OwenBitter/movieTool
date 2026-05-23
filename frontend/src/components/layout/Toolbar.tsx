import { useState } from 'react';
import { Input, Select, Button, Segmented, Tag, Rate, Popover, Space } from 'antd';
import {
  SearchOutlined, ExportOutlined, TagsOutlined, ThunderboltOutlined,
  CloudServerOutlined, FilterOutlined, CloseOutlined,
} from '@ant-design/icons';
import { useStore } from '../../store';
import { exportMoviesCSV } from '../../api';

interface ToolbarProps {
  onTagManager: () => void;
  onQuickRate: () => void;
  onBackup: () => void;
}

export function Toolbar({ onTagManager, onQuickRate, onBackup }: ToolbarProps) {
  const movies = useStore((s) => s.movies);
  const viewMode = useStore((s) => s.viewMode);
  const tagsConfig = useStore((s) => s.tagsConfig);
  const filterPanelOpen = useStore((s) => s.filterPanelOpen);
  const setSearch = useStore((s) => s.setSearch);
  const setSort = useStore((s) => s.setSort);
  const setViewMode = useStore((s) => s.setViewMode);
  const toggleFilterPanel = useStore((s) => s.toggleFilterPanel);
  const setRating = useStore((s) => s.setRating);
  const setStatus = useStore((s) => s.setStatus);
  const toggleTag = useStore((s) => s.toggleTag);
  const clearFilters = useStore((s) => s.clearFilters);
  const hasFilters = movies.rating > 0 || movies.status || movies.tags.length > 0;

  const handleExport = async () => {
    try {
      const params: Record<string, string> = {};
      if (movies.actor) params.actor = movies.actor;
      if (movies.tags.length > 0) params.tags = movies.tags.join(',');
      if (movies.rating > 0) params.rating = String(movies.rating);
      if (movies.status) params.status = movies.status;
      if (movies.search) params.search = movies.search;
      params.sort = movies.sort;
      const blob = await exportMoviesCSV(params);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'movies.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Export failed:', e);
    }
  };

  const chips: { key: string; label: string }[] = [];
  if (movies.rating > 0) chips.push({ key: 'rating', label: `⭐ ≥${movies.rating}` });
  if (movies.status) chips.push({ key: 'status', label: movies.status === 'classified' ? '✅ 已分类' : '⬜ 未分类' });
  movies.tags.forEach((t) => chips.push({ key: `tag:${t}`, label: t }));

  const usage = tagsConfig?.usage || {};
  const attrTags = tagsConfig?.available_tags || [];
  const typeTags = tagsConfig?.type_tags || [];
  const customTags = tagsConfig?.custom_tags || [];
  const [filterSearch, setFilterSearch] = useState('');

  const filterTagSearch = filterSearch.toLowerCase();
  const filterAttrTags = filterTagSearch ? attrTags.filter((t) => t.toLowerCase().includes(filterTagSearch)) : attrTags;
  const filterTypeTags = filterTagSearch ? typeTags.filter((t) => t.toLowerCase().includes(filterTagSearch)) : typeTags;
  const filterCustomTags = filterTagSearch ? customTags.filter((t) => t.toLowerCase().includes(filterTagSearch)) : customTags;

  const filterPopover = (
    <div className="filter-popover">
      <div style={{ marginBottom: 10 }}>
        <Input
          placeholder="搜索标签..."
          value={filterSearch}
          onChange={(e) => setFilterSearch(e.target.value)}
          allowClear
          size="small"
          onClick={(e) => e.stopPropagation()}
        />
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, color: '#88889a', marginBottom: 4 }}>⭐ 最低评分</div>
        <Rate value={movies.rating} onChange={setRating} allowClear style={{ fontSize: 18 }} />
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, color: '#88889a', marginBottom: 4 }}>📌 状态</div>
        <Space size={4}>
          <Tag color={!movies.status ? 'gold' : 'default'} style={{ cursor: 'pointer' }} onClick={() => setStatus('')}>全部</Tag>
          <Tag color={movies.status === 'classified' ? 'gold' : 'default'} style={{ cursor: 'pointer' }} onClick={() => setStatus(movies.status === 'classified' ? '' : 'classified')}>已分类</Tag>
          <Tag color={movies.status === 'new' ? 'gold' : 'default'} style={{ cursor: 'pointer' }} onClick={() => setStatus(movies.status === 'new' ? '' : 'new')}>未分类</Tag>
        </Space>
      </div>
      {filterAttrTags.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, color: '#88889a', marginBottom: 4 }}>📌 属性标签</div>
          <div className="filter-tag-list">
            {filterAttrTags.map((t) => (
              <Tag key={t} color={movies.tags.includes(t) ? 'gold' : 'default'} style={{ cursor: 'pointer', margin: 0 }} onClick={() => toggleTag(t)}>
                {t}{usage[t] ? ` ${usage[t]}` : ''}
              </Tag>
            ))}
          </div>
        </div>
      )}
      {filterTypeTags.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, color: '#88889a', marginBottom: 4 }}>🎬 类型标签</div>
          <div className="filter-tag-list">
            {filterTypeTags.map((t) => (
              <Tag key={t} color={movies.tags.includes(t) ? 'gold' : 'default'} style={{ cursor: 'pointer', margin: 0 }} onClick={() => toggleTag(t)}>
                {t}{usage[t] ? ` ${usage[t]}` : ''}
              </Tag>
            ))}
          </div>
        </div>
      )}
      {filterCustomTags.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: '#88889a', marginBottom: 4 }}>🏷 自定义标签</div>
          <div className="filter-tag-list">
            {filterCustomTags.map((t) => (
              <Tag key={t} color={movies.tags.includes(t) ? 'gold' : 'default'} style={{ cursor: 'pointer', margin: 0 }} onClick={() => toggleTag(t)}>
                {t}{usage[t] ? ` ${usage[t]}` : ''}
              </Tag>
            ))}
          </div>
        </div>
      )}
      {filterSearch && filterAttrTags.length === 0 && filterTypeTags.length === 0 && filterCustomTags.length === 0 && (
        <div style={{ color: '#555', fontSize: 12, textAlign: 'center', padding: 12 }}>无匹配标签</div>
      )}
    </div>
  );

  return (
    <div className="toolbar">
      <Input
        prefix={<SearchOutlined style={{ color: '#666678' }} />}
        placeholder="搜索番号 / 演员 / 片名..."
        value={movies.search}
        onChange={(e) => setSearch(e.target.value)}
        allowClear
        style={{ width: 200 }}
      />

      <Popover
        content={filterPopover}
        trigger="click"
        open={filterPanelOpen}
        onOpenChange={(v) => { if (v !== filterPanelOpen) toggleFilterPanel(); }}
        placement="bottomLeft"
      >
        <Button type={hasFilters ? 'primary' : 'text'} icon={<FilterOutlined />} size="small">
          筛选{hasFilters ? ` ${chips.length}` : ''}
        </Button>
      </Popover>

      {chips.map((c) => (
        <Tag
          key={c.key}
          closable
          color="gold"
          style={{ margin: 0 }}
          onClose={() => {
            if (c.key === 'rating') setRating(0);
            else if (c.key === 'status') setStatus('');
            else toggleTag(c.key.replace('tag:', ''));
          }}
        >
          {c.label}
        </Tag>
      ))}

      {hasFilters && (
        <Button size="small" type="text" onClick={clearFilters} icon={<CloseOutlined />} style={{ color: '#88889a' }}>
          清除
        </Button>
      )}

      <div style={{ flex: 1 }} />

      <Select
        value={movies.sort}
        onChange={(v) => setSort(v)}
        style={{ width: 140 }}
        options={[
          { value: 'time', label: '🕐 下载时间' },
          { value: 'rating', label: '⭐ 评分' },
          { value: 'name', label: '📛 名称' },
        ]}
      />
      <Segmented
        value={viewMode}
        onChange={(v) => setViewMode(v as 'card' | 'table')}
        options={[
          { value: 'card', label: '🟫 卡片' },
          { value: 'table', label: '📋 表格' },
        ]}
      />
      <Button icon={<ExportOutlined />} onClick={handleExport}>导出</Button>
      <Button icon={<ThunderboltOutlined />} onClick={onQuickRate}>快速评分</Button>
      <Button icon={<CloudServerOutlined />} onClick={onBackup}>备份</Button>
      <Button icon={<TagsOutlined />} onClick={onTagManager}>标签管理</Button>
    </div>
  );
}
