import { Button, Tag } from 'antd';
import { FilterOutlined, CloseOutlined } from '@ant-design/icons';
import { useAppState } from '../../context/AppContext';

export function FilterBar() {
  const { state, dispatch } = useAppState();
  const m = state.movies;
  const hasFilters = m.rating > 0 || m.status || m.tags.length > 0;

  const chips: { key: string; label: string }[] = [];
  if (m.rating > 0) chips.push({ key: 'rating', label: `⭐ ≥${m.rating}` });
  if (m.status) chips.push({ key: 'status', label: `📌 ${m.status === 'classified' ? '已分类' : '未分类'}` });
  m.tags.forEach((t) => chips.push({ key: `tag:${t}`, label: `🏷 ${t}` }));

  return (
    <div className="filter-bar">
      <Button
        type="text"
        icon={<FilterOutlined />}
        onClick={() => dispatch({ type: 'TOGGLE_FILTER_PANEL' })}
        style={{ color: '#e8b84b' }}
      >
        筛选条件
      </Button>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', flex: 1 }}>
        {chips.map((c) => (
          <Tag
            key={c.key}
            closable
            color="gold"
            onClose={() => {
              if (c.key === 'rating') dispatch({ type: 'SET_RATING', rating: 0 });
              else if (c.key === 'status') dispatch({ type: 'SET_STATUS', status: '' });
              else {
                const tagName = c.key.replace('tag:', '');
                dispatch({ type: 'TOGGLE_TAG', tag: tagName });
              }
            }}
          >
            {c.label}
          </Tag>
        ))}
      </div>
      {hasFilters && (
        <Button size="small" type="text" onClick={() => dispatch({ type: 'CLEAR_FILTERS' })} icon={<CloseOutlined />}>
          清除全部
        </Button>
      )}
    </div>
  );
}
