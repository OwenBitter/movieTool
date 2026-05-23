import { Input, Tooltip } from 'antd';
import { SearchOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useStore } from '../../store';
import { useActors } from '../../hooks/useActors';

interface ActorSidebarProps {
  onActressDetail: (name: string) => void;
}

export function ActorSidebar({ onActressDetail }: ActorSidebarProps) {
  const actors = useStore((s) => s.actors);
  const actorFilter = useStore((s) => s.movies.actor);
  const setActor = useStore((s) => s.setActor);
  const { actorSearch, setActorSearch } = useActors();

  const searchL = actorSearch.toLowerCase();
  const filtered = searchL
    ? actors.filter((a) => a.name.toLowerCase().includes(searchL))
    : actors;

  const totalCount = actors.reduce((s, a) => s + a.count, 0);

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
          className={`actor-item all${!actorFilter ? ' active' : ''}`}
          onClick={() => setActor('')}
        >
          <span>📂 全部影片</span>
          <span className="count">{totalCount}</span>
        </div>
        {filtered.map((a) => (
          <div
            key={a.name}
            className={`actor-item${actorFilter === a.name ? ' active' : ''}`}
          >
            <span
              style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
              onClick={() => setActor(a.name)}
            >
              {a.name}
            </span>
            <Tooltip title="查看详情">
              <InfoCircleOutlined
                style={{ marginRight: 6, color: '#88889a', fontSize: 12, cursor: 'pointer' }}
                onClick={(e) => { e.stopPropagation(); onActressDetail(a.name); }}
              />
            </Tooltip>
            <span className="count">{a.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
