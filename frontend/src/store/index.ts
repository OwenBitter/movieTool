import { create } from 'zustand';
import { debounce } from 'lodash';
import type { Actor, Movie, MovieFilters, TagConfig, Stats, SortField, ViewMode } from '../types';
import type { ThemeMode } from '../styles/theme';
import * as api from '../api';

interface AppState {
  // Data
  theme: ThemeMode;
  actors: Actor[];
  tagsConfig: TagConfig | null;
  stats: Stats | null;
  movieList: Movie[];

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

  // Async actions
  fetchMovies: () => Promise<void>;
  fetchActors: () => Promise<void>;
  fetchTags: () => Promise<void>;
  fetchStats: () => Promise<void>;
  refreshAll: () => Promise<void>;
}

const storedTheme = (localStorage.getItem('theme') as ThemeMode) || 'dark';

export const useStore = create<AppState>((set, get) => ({
  theme: storedTheme,
  actors: [],
  tagsConfig: null,
  stats: null,
  movieList: [],
  selected: new Set(),
  viewMode: 'card' as ViewMode,
  filterPanelOpen: false,
  loading: false,
  movies: { actor: '', tags: [], rating: 0, status: '', search: '', sort: 'time' as SortField, sizeMin: null, sizeMax: null, dateFrom: '', dateTo: '' },

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

  setSizeMin: (val: number | null) =>
    set((s) => ({ movies: { ...s.movies, sizeMin: val } })),

  setSizeMax: (val: number | null) =>
    set((s) => ({ movies: { ...s.movies, sizeMax: val } })),

  setDateFrom: (val: string) =>
    set((s) => ({ movies: { ...s.movies, dateFrom: val } })),

  setDateTo: (val: string) =>
    set((s) => ({ movies: { ...s.movies, dateTo: val } })),

  setSort: (sort) =>
    set((s) => ({ movies: { ...s.movies, sort } })),

  setViewMode: (mode) => set({ viewMode: mode }),
  toggleView: () => set((s) => ({ viewMode: s.viewMode === 'card' ? 'table' : 'card' })),
  toggleFilterPanel: () => set((s) => ({ filterPanelOpen: !s.filterPanelOpen })),

  setSelected: (ids) => set({ selected: ids }),

  clearFilters: () =>
    set({
      movies: { actor: '', tags: [], rating: 0, status: '', search: '', sort: 'time', sizeMin: null, sizeMax: null, dateFrom: '', dateTo: '' },
    }),

  setLoading: (loading) => set({ loading }),

  fetchMovies: debounce(async () => {
    const { movies: filters } = get();
    set({ loading: true });
    try {
      const params: Record<string, string> = {};
      if (filters.actor) params.actor = filters.actor;
      if (filters.tags.length > 0) params.tags = filters.tags.join(',');
      if (filters.rating > 0) params.rating = String(filters.rating);
      if (filters.status) params.status = filters.status;
      if (filters.search) params.search = filters.search;
      params.sort = filters.sort;
      const result = await api.fetchMovies(params);
      set({ movieList: result.movies });
    } catch (e) {
      console.error('Failed to fetch movies:', e);
    } finally {
      set({ loading: false });
    }
  }, 300),

  fetchActors: async () => {
    try {
      const actors = await api.fetchActors();
      set({ actors });
    } catch (e) {
      console.error('Failed to fetch actors:', e);
    }
  },

  fetchTags: async () => {
    try {
      const config = await api.fetchTags();
      set({ tagsConfig: config });
    } catch (e) {
      console.error('Failed to fetch tags:', e);
    }
  },

  fetchStats: async () => {
    try {
      const stats = await api.fetchStats();
      set({ stats });
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  },

  refreshAll: async () => {
    const { fetchMovies, fetchActors, fetchTags, fetchStats } = get();
    await Promise.all([fetchMovies(), fetchActors(), fetchTags(), fetchStats()]);
  },
}));
