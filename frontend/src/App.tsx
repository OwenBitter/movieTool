import { useState, useCallback, useEffect, Suspense, lazy } from 'react';
import { Layout, Spin } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import { AppHeader } from './components/layout/AppHeader';
import { ActorSidebar } from './components/layout/ActorSidebar';
import { Toolbar } from './components/layout/Toolbar';
import { MovieGridView } from './components/movies/MovieGridView';
import { MovieTable } from './components/movies/MovieTable';
import { BatchToolbar } from './components/batch/BatchToolbar';
import { BatchDialog } from './components/batch/BatchDialog';
import { QuickRate } from './components/rating/QuickRate';
import { ActressDetail } from './components/actress/ActressDetail';
import { BackupManager } from './components/backup/BackupManager';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { useMovies } from './hooks/useMovies';
import { useStore } from './store';

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
  const theme = useStore((s) => s.theme);
  const viewMode = useStore((s) => s.viewMode);
  const selected = useStore((s) => s.selected);
  const actorFilter = useStore((s) => s.movies.actor);
  const toggleView = useStore((s) => s.toggleView);
  const { movies, reload } = useMovies();
  const [tagManagerOpen, setTagManagerOpen] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);
  const [quickRateOpen, setQuickRateOpen] = useState(false);
  const [actressDetail, setActressDetail] = useState<string | null>(null);
  const [backupOpen, setBackupOpen] = useState(false);
  const [batchMode, setBatchMode] = useState<'delete' | 'move' | 'copy' | 'tags' | null>(null);

  const handleUpdated = useCallback(() => {
    reload();
  }, [reload]);

  const fetchActors = useStore((s) => s.fetchActors);
  const fetchTags = useStore((s) => s.fetchTags);
  const fetchStats = useStore((s) => s.fetchStats);

  // Initial data load
  useEffect(() => {
    fetchActors();
    fetchTags();
    fetchStats();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync theme to <html> data attribute for CSS
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

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
          toggleView();
          break;
        case 'escape':
          setTagManagerOpen(false);
          setStatsOpen(false);
          setQuickRateOpen(false);
          setBatchMode(null);
          break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [toggleView]);

  return (
    <ErrorBoundary>
      <Layout style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppHeader />
        <Toolbar
          onTagManager={() => setTagManagerOpen(true)}
          onQuickRate={() => setQuickRateOpen(true)}
          onBackup={() => setBackupOpen(true)}
        />
        <BatchToolbar movies={movies} onBatch={setBatchMode} />

        <Layout style={{ flex: 1, overflow: 'hidden' }}>
          <Sider
            width={220}
            style={{ overflow: 'hidden', borderRight: '1px solid rgba(255,255,255,0.05)' }}
          >
            <ActorSidebar onActressDetail={setActressDetail} />
          </Sider>

          <Content style={{ overflow: 'auto', background: '#08080c' }}>
            <div className="content-header">
              <h2>{actorFilter || '全部影片'}</h2>
              <span style={{ color: '#88889a', fontSize: 13 }}>{movies.length} 部</span>
              {selected.size > 0 && (
                <span style={{ color: '#e8b84b', fontSize: 13 }}>
                  已选 {selected.size} 部
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

            {viewMode === 'card' ? (
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

        <QuickRate open={quickRateOpen} onClose={() => { setQuickRateOpen(false); reload(); }} />
        <ActressDetail name={actressDetail} onClose={() => setActressDetail(null)} />
        <BackupManager open={backupOpen} onClose={() => setBackupOpen(false)} />
        <BatchDialog
          open={batchMode !== null}
          mode={batchMode}
          count={selected.size}
          selectedIds={[...selected]}
          onClose={() => setBatchMode(null)}
          onDone={handleUpdated}
        />
      </Layout>
    </ErrorBoundary>
  );
}
