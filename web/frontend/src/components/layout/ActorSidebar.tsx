import { Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useAppState } from '../../context/AppContext';
import { useActors } from '../../hooks/useActors';

export function ActorSidebar() {
  const { state, dispatch } = useAppState();
  const { actorSearch, setActorSearch } = useActors();

  const searchL = actorSearch.toLowerCase();
  const filtered = searchL
    ? state.actors.filter((a) => a.name.toLowerCase().includes(searchL))
    : state.actors;

  const totalCount = state.actors.reduce((s, a) => s + a.count, 0);

  return (
    <div className="sidebar">
      <div className="sidebar-title">
        演员列表 <span style={{ color: '#88889a', fontWeight: 400 }}>({filtered.length}人)</span>
      </div>
      <div className="sidebar-search">
        <Input
          prefix={<SearchOutlined style={{ color: '#666678' }} />}
          placeholder="搜索演员..."
          value={actorSearch}
          onChange={(e) => setActorSearch(e.target.value)}
          allowClear
          size="small"
        />
      </div>
      <div className="sidebar-list">
        <div
          className={`actor-item all${!state.movies.actor ? ' active' : ''}`}
          onClick={() => dispatch({ type: 'SET_ACTOR', actor: '' })}
        >
          <span>📂 全部影片</span>
          <span className="count">{totalCount}</span>
        </div>
        {filtered.map((a) => (
          <div
            key={a.name}
            className={`actor-item${state.movies.actor === a.name ? ' active' : ''}`}
            onClick={() => dispatch({ type: 'SET_ACTOR', actor: a.name })}
          >
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {a.name}
            </span>
            <span className="count">{a.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
