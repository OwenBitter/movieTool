import { useState, useCallback } from 'react';
import { Layout } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import { AppHeader } from './components/layout/AppHeader';
import { ActorSidebar } from './components/layout/ActorSidebar';
import { Toolbar } from './components/layout/Toolbar';
import { FilterBar } from './components/filters/FilterBar';
import { FilterPanel } from './components/filters/FilterPanel';
import { MovieGridView } from './components/movies/MovieGridView';
import { MovieTable } from './components/movies/MovieTable';
import { TagManager } from './components/tags/TagManager';
import { BatchToolbar } from './components/batch/BatchToolbar';
import { BatchDialog } from './components/batch/BatchDialog';
import { StatsDashboard } from './components/stats/StatsDashboard';
import { useMovies } from './hooks/useMovies';
import { useAppState } from './context/AppContext';

const { Sider, Content } = Layout;

export default function App() {
  const { state } = useAppState();
  const { movies, reload } = useMovies();
  const [tagManagerOpen, setTagManagerOpen] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);
  const [batchMode, setBatchMode] = useState<'delete' | 'move' | 'copy' | null>(null);

  const handleUpdated = useCallback(() => {
    reload();
  }, [reload]);

  return (
    <Layout style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top: Header */}
      <AppHeader />

      {/* Toolbar */}
      <Toolbar onTagManager={() => setTagManagerOpen(true)} />

      {/* Filter bar */}
      <FilterBar />

      {/* Filter panel */}
      <FilterPanel />

      {/* Batch toolbar */}
      <BatchToolbar totalCount={movies.length} onBatch={setBatchMode} />

      {/* Main content area */}
      <Layout style={{ flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <Sider
          width={220}
          style={{ overflow: 'hidden', borderRight: '1px solid rgba(255,255,255,0.05)' }}
        >
          <ActorSidebar />
        </Sider>

        {/* Content */}
        <Content style={{ overflow: 'auto', background: '#08080c' }}>
          {/* Content header */}
          <div className="content-header">
            <h2>
              {state.movies.actor || '全部影片'}
            </h2>
            <span style={{ color: '#88889a', fontSize: 13 }}>{movies.length} 部</span>
            {state.selected.size > 0 && (
              <span style={{ color: '#e8b84b', fontSize: 13 }}>
                已选 {state.selected.size} 部
              </span>
            )}
            <div style={{ marginLeft: 'auto' }}>
              <span
                onClick={() => setStatsOpen(true)}
                style={{ cursor: 'pointer', color: '#e8b84b', fontSize: 18, padding: '4px 8px' }}
                title="统计面板"
              >
                <BarChartOutlined />
              </span>
            </div>
          </div>

          {/* View */}
          {state.viewMode === 'card' ? (
            <div style={{ padding: '0 20px' }}>
              <MovieGridView movies={movies} onUpdated={handleUpdated} />
            </div>
          ) : (
            <MovieTable movies={movies} onUpdated={handleUpdated} />
          )}
        </Content>
      </Layout>

      {/* Tag Manager Modal */}
      <TagManager open={tagManagerOpen} onClose={() => setTagManagerOpen(false)} />

      {/* Stats Dashboard Modal */}
      <StatsDashboard open={statsOpen} onClose={() => setStatsOpen(false)} />

      {/* Batch Dialog */}
      <BatchDialog
        open={batchMode !== null}
        mode={batchMode}
        count={state.selected.size}
        selectedIds={[...state.selected]}
        onClose={() => setBatchMode(null)}
        onDone={handleUpdated}
      />
    </Layout>
  );
}
