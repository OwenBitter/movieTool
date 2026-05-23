import { Typography, Button, Tooltip } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useStore } from '../../store';
import { useTags } from '../../hooks/useTags';

export function AppHeader() {
  const stats = useStore((s) => s.stats);
  const theme = useStore((s) => s.theme);
  const toggleTheme = useStore((s) => s.toggleTheme);
  useTags();
  const isDark = theme === 'dark';

  return (
    <div className="app-header">
      <Typography.Title level={4} style={{ margin: 0, color: isDark ? '#e8e8ee' : '#1a1a2e' }}>
        🎬 电影分类浏览器
      </Typography.Title>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div className="header-stats" style={{ color: isDark ? '#88889a' : '#666678' }}>
          {stats
            ? `${stats.total} 部 · ${stats.actors_count} 位演员 · ${stats.classified} 已分类 · ${stats.rated} 已评分 · ${stats.tagged} 有标签`
            : '加载中...'}
        </div>
        <Tooltip title={isDark ? '切换亮色主题' : '切换暗色主题'}>
          <Button
            size="small"
            type="text"
            icon={isDark ? <SunOutlined /> : <MoonOutlined />}
            onClick={toggleTheme}
            style={{ color: isDark ? '#e8b84b' : '#d4a63a' }}
          />
        </Tooltip>
      </div>
    </div>
  );
}
