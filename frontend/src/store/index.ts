import { create } from 'zustand';
import type { Actor, MovieFilters, TagConfig, Stats, SortField, ViewMode } from '../types';
import type { ThemeMode } from '../styles/theme';

interface AppState {
  // Data
  theme: ThemeMode;
  actors: Actor[];
  tagsConfig: TagConfig | null;
  stats: Stats | null;

  // UI
  selected: Set<string>;
  viewMode: ViewMode;
  filterPanelOpen: boolean;
  loading: boolean;

  // Filters
  movies: MovieFilters;

  // Actions
  toggleTheme: () => void;
  setActors: (actors: Actor[]) => void;
  setTagsConfig: (config: TagConfig) => void;
  setStats: (stats: Stats) => void;
  setActor: (actor: string) => void;
  toggleTag: (tag: string) => void;
  setTags: (tags: string[]) => void;
  setRating: (rating: number) => void;
  setStatus: (status: string) => void;
  setSearch: (search: string) => void;
  setSort: (sort: SortField) => void;
  setViewMode: (mode: ViewMode) => void;
  toggleView: () => void;
  toggleFilterPanel: () => void;
  setSelected: (ids: Set<string>) => void;
  clearFilters: () => void;
  setLoading: (loading: boolean) => void;
}

const storedTheme = (localStorage.getItem('theme') as ThemeMode) || 'dark';

export const useStore = create<AppState>((set) => ({
  theme: storedTheme,
  actors: [],
  tagsConfig: null,
  stats: null,
  selected: new Set(),
  viewMode: 'card' as ViewMode,
  filterPanelOpen: false,
  loading: false,
  movies: { actor: '', tags: [], rating: 0, status: '', search: '', sort: 'time' as SortField },

  toggleTheme: () =>
    set((s) => {
      const next = s.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      return { theme: next };
    }),

  setActors: (actors) => set({ actors }),
  setTagsConfig: (config) => set({ tagsConfig: config }),
  setStats: (stats) => set({ stats }),

  setActor: (actor) =>
    set((s) => ({ movies: { ...s.movies, actor } })),

  toggleTag: (tag) =>
    set((s) => ({
      movies: {
        ...s.movies,
        tags: s.movies.tags.includes(tag)
          ? s.movies.tags.filter((t) => t !== tag)
          : [...s.movies.tags, tag],
      },
    })),

  setTags: (tags) =>
    set((s) => ({ movies: { ...s.movies, tags } })),

  setRating: (rating) =>
    set((s) => ({ movies: { ...s.movies, rating } })),

  setStatus: (status) =>
    set((s) => ({ movies: { ...s.movies, status } })),

  setSearch: (search) =>
    set((s) => ({ movies: { ...s.movies, search } })),

  setSort: (sort) =>
    set((s) => ({ movies: { ...s.movies, sort } })),

  setViewMode: (mode) => set({ viewMode: mode }),
  toggleView: () => set((s) => ({ viewMode: s.viewMode === 'card' ? 'table' : 'card' })),
  toggleFilterPanel: () => set((s) => ({ filterPanelOpen: !s.filterPanelOpen })),

  setSelected: (ids) => set({ selected: ids }),

  clearFilters: () =>
    set({
      movies: { actor: '', tags: [], rating: 0, status: '', search: '', sort: 'time' },
    }),

  setLoading: (loading) => set({ loading }),
}));
