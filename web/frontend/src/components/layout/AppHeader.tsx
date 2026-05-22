import { Typography } from 'antd';
import { useAppState } from '../../context/AppContext';
import { useTags } from '../../hooks/useTags';

export function AppHeader() {
  const { state } = useAppState();
  useTags(); // init tags + stats

  return (
    <div className="app-header">
      <Typography.Title level={4} style={{ margin: 0, color: '#e8e8ee' }}>
        🎬 电影分类浏览器
      </Typography.Title>
      <div className="header-stats">
        {state.stats
          ? `${state.stats.total} 部 · ${state.stats.actors_count} 位演员 · ${state.stats.classified} 已分类 · ${state.stats.rated} 已评分 · ${state.stats.tagged} 有标签`
          : '加载中...'}
      </div>
    </div>
  );
}
