import { Input, Select, Button, Segmented } from 'antd';
import { SearchOutlined, ExportOutlined, TagsOutlined } from '@ant-design/icons';
import { useAppState } from '../../context/AppContext';
import { exportMoviesCSV } from '../../api';

interface ToolbarProps {
  onTagManager: () => void;
}

export function Toolbar({ onTagManager }: ToolbarProps) {
  const { state, dispatch } = useAppState();

  const handleExport = async () => {
    try {
      const params: Record<string, string> = {};
      if (state.movies.actor) params.actor = state.movies.actor;
      if (state.movies.tags.length > 0) params.tags = state.movies.tags.join(',');
      if (state.movies.rating > 0) params.rating = String(state.movies.rating);
      if (state.movies.status) params.status = state.movies.status;
      if (state.movies.search) params.search = state.movies.search;
      params.sort = state.movies.sort;

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

  return (
    <div className="toolbar">
      <Input
        prefix={<SearchOutlined style={{ color: '#666678' }} />}
        placeholder="🔍 搜索番号 / 演员 / 片名..."
        value={state.movies.search}
        onChange={(e) => dispatch({ type: 'SET_SEARCH', search: e.target.value })}
        allowClear
        style={{ width: 240 }}
      />
      <Select
        value={state.movies.sort}
        onChange={(v) => dispatch({ type: 'SET_SORT', sort: v })}
        style={{ width: 140 }}
        options={[
          { value: 'time', label: '🕐 下载时间' },
          { value: 'rating', label: '⭐ 评分' },
          { value: 'name', label: '📛 名称' },
        ]}
      />
      <Segmented
        value={state.viewMode}
        onChange={(v) => dispatch({ type: 'SET_VIEW_MODE', mode: v as 'card' | 'table' })}
        options={[
          { value: 'card', label: '🟫 卡片' },
          { value: 'table', label: '📋 表格' },
        ]}
      />
      <Button icon={<ExportOutlined />} onClick={handleExport}>
        导出
      </Button>
      <Button icon={<TagsOutlined />} onClick={onTagManager}>
        标签管理
      </Button>
    </div>
  );
}
