import { Button, Tag, Rate } from 'antd';
import { useAppState } from '../../context/AppContext';

export function FilterPanel() {
  const { state, dispatch } = useAppState();

  if (!state.filterPanelOpen) return null;

  const tagConfig = state.tagsConfig;
  if (!tagConfig) return null;

  const usage = tagConfig.usage || {};

  return (
    <div className="filter-panel">
      {/* Star rating filter */}
      <div style={{ marginBottom: 16 }}>
        <div className="filter-section-title">⭐ 最低评分</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Rate
            value={state.movies.rating}
            onChange={(v) => dispatch({ type: 'SET_RATING', rating: v })}
            allowClear
          />
          {state.movies.rating > 0 && (
            <Button size="small" type="text" onClick={() => dispatch({ type: 'SET_RATING', rating: 0 })}>
              ✕
            </Button>
          )}
        </div>
      </div>

      {/* Status filter */}
      <div style={{ marginBottom: 16 }}>
        <div className="filter-section-title">📌 状态</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Tag
            color={!state.movies.status ? 'gold' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() => dispatch({ type: 'SET_STATUS', status: '' })}
          >
            全部
          </Tag>
          <Tag
            color={state.movies.status === 'classified' ? 'gold' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() =>
              dispatch({ type: 'SET_STATUS', status: state.movies.status === 'classified' ? '' : 'classified' })
            }
          >
            已分类
          </Tag>
          <Tag
            color={state.movies.status === 'new' ? 'gold' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() =>
              dispatch({ type: 'SET_STATUS', status: state.movies.status === 'new' ? '' : 'new' })
            }
          >
            未分类
          </Tag>
        </div>
      </div>

      {/* Attribute tags */}
      {tagConfig.available_tags.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div className="filter-section-title">📌 属性标签</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {tagConfig.available_tags.map((t) => {
              const active = state.movies.tags.includes(t);
              return (
                <Tag
                  key={t}
                  color={active ? 'gold' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => dispatch({ type: 'TOGGLE_TAG', tag: t })}
                >
                  {t} {usage[t] ? `(${usage[t]})` : ''}
                </Tag>
              );
            })}
          </div>
        </div>
      )}

      {/* Type tags */}
      {tagConfig.type_tags.length > 0 && (
        <div>
          <div className="filter-section-title">🎬 类型标签</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {tagConfig.type_tags.map((t) => {
              const active = state.movies.tags.includes(t);
              return (
                <Tag
                  key={t}
                  color={active ? 'gold' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => dispatch({ type: 'TOGGLE_TAG', tag: t })}
                >
                  {t} {usage[t] ? `(${usage[t]})` : ''}
                </Tag>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
