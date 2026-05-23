import { useState, useCallback, useEffect, Suspense, lazy } from 'react';
import { Layout, Spin } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import { AppHeader } from './components/layout/AppHeader';
import { ActorSidebar } from './components/layout/ActorSidebar';
import { Toolbar } from './components/layout/Toolbar';
import { FilterBar } from './components/filters/FilterBar';
import { FilterPanel } from './components/filters/FilterPanel';
import { MovieGridView } from './components/movies/MovieGridView';
import { MovieTable } from './components/movies/MovieTable';
import { BatchToolbar } from './components/batch/BatchToolbar';
import { BatchDialog } from './components/batch/BatchDialog';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { useMovies } from './hooks/useMovies';
import { useAppState } from './context/AppContext';

const TagManager = lazy(() => import('./components/tags/TagManager').then(m => ({ default: m.TagManager })));
const StatsDashboard = lazy(() => import('./components/stats/StatsDashboard').then(m => ({ default: m.StatsDashboard })));

const { Sider, Content } = Layout;

function SuspenseFallback() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
      <Spin size="large" />
    </div>
  );
}

export default function App() {
  const { state, dispatch } = useAppState();
  const { movies, reload } = useMovies();
  const [tagManagerOpen, setTagManagerOpen] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);
  const [batchMode, setBatchMode] = useState<'delete' | 'move' | 'copy' | null>(null);

  const handleUpdated = useCallback(() => {
    reload();
  }, [reload]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key.toLowerCase()) {
        case 'f':
          e.preventDefault();
          document.querySelector<HTMLInputElement>('.filter-bar input')?.focus();
          break;
        case 'g':
          dispatch({ type: 'TOGGLE_VIEW' });
          break;
        case 'escape':
          setTagManagerOpen(false);
          setStatsOpen(false);
          setBatchMode(null);
          break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [dispatch]);

  return (
    <ErrorBoundary>
      <Layout style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppHeader />
        <Toolbar onTagManager={() => setTagManagerOpen(true)} />
        <div className="filter-bar">
          <FilterBar />
        </div>
        <FilterPanel />
        <BatchToolbar movies={movies} onBatch={setBatchMode} />

        <Layout style={{ flex: 1, overflow: 'hidden' }}>
          <Sider
            width={220}
            style={{ overflow: 'hidden', borderRight: '1px solid rgba(255,255,255,0.05)' }}
          >
            <ActorSidebar />
          </Sider>

          <Content style={{ overflow: 'auto', background: '#08080c' }}>
            <div className="content-header">
              <h2>{state.movies.actor || '全部影片'}</h2>
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

            {state.viewMode === 'card' ? (
              <div style={{ padding: '0 20px' }}>
                <MovieGridView movies={movies} onUpdated={handleUpdated} />
              </div>
            ) : (
              <MovieTable movies={movies} onUpdated={handleUpdated} />
            )}
          </Content>
        </Layout>

        <Suspense fallback={<SuspenseFallback />}>
          <TagManager open={tagManagerOpen} onClose={() => setTagManagerOpen(false)} />
        </Suspense>
        <Suspense fallback={<SuspenseFallback />}>
          <StatsDashboard open={statsOpen} onClose={() => setStatsOpen(false)} />
        </Suspense>

        <BatchDialog
          open={batchMode !== null}
          mode={batchMode}
          count={state.selected.size}
          selectedIds={[...state.selected]}
          onClose={() => setBatchMode(null)}
          onDone={handleUpdated}
        />
      </Layout>
    </ErrorBoundary>
  );
}
