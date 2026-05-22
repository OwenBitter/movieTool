import React, { createContext, useContext, useCallback, useRef } from 'react';
import type { Actor, MovieFilters, TagConfig, Stats, SortField, ViewMode } from '../types';

interface AppState {
  actors: Actor[];
  movies: MovieFilters;
  tagsConfig: TagConfig | null;
  stats: Stats | null;
  selected: Set<string>;
  viewMode: ViewMode;
  filterPanelOpen: boolean;
  loading: boolean;
}

type AppAction =
  | { type: 'SET_ACTORS'; actors: Actor[] }
  | { type: 'SET_TAGS_CONFIG'; config: TagConfig }
  | { type: 'SET_STATS'; stats: Stats }
  | { type: 'SET_ACTOR'; actor: string }
  | { type: 'TOGGLE_TAG'; tag: string }
  | { type: 'SET_TAGS'; tags: string[] }
  | { type: 'SET_RATING'; rating: number }
  | { type: 'SET_STATUS'; status: string }
  | { type: 'SET_SEARCH'; search: string }
  | { type: 'SET_SORT'; sort: SortField }
  | { type: 'SET_VIEW_MODE'; mode: ViewMode }
  | { type: 'TOGGLE_FILTER_PANEL' }
  | { type: 'SET_SELECTED'; ids: Set<string> }
  | { type: 'CLEAR_FILTERS' }
  | { type: 'SET_LOADING'; loading: boolean };

const initialState: AppState = {
  actors: [],
  movies: { actor: '', tags: [], rating: 0, status: '', search: '', sort: 'time' },
  tagsConfig: null,
  stats: null,
  selected: new Set(),
  viewMode: 'card',
  filterPanelOpen: false,
  loading: false,
};

function reducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_ACTORS':
      return { ...state, actors: action.actors };
    case 'SET_TAGS_CONFIG':
      return { ...state, tagsConfig: action.config };
    case 'SET_STATS':
      return { ...state, stats: action.stats };
    case 'SET_ACTOR':
      return { ...state, movies: { ...state.movies, actor: action.actor } };
    case 'TOGGLE_TAG': {
      const tags = state.movies.tags.includes(action.tag)
        ? state.movies.tags.filter((t) => t !== action.tag)
        : [...state.movies.tags, action.tag];
      return { ...state, movies: { ...state.movies, tags } };
    }
    case 'SET_TAGS':
      return { ...state, movies: { ...state.movies, tags: action.tags } };
    case 'SET_RATING':
      return { ...state, movies: { ...state.movies, rating: action.rating } };
    case 'SET_STATUS':
      return { ...state, movies: { ...state.movies, status: action.status } };
    case 'SET_SEARCH':
      return { ...state, movies: { ...state.movies, search: action.search } };
    case 'SET_SORT':
      return { ...state, movies: { ...state.movies, sort: action.sort } };
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.mode };
    case 'TOGGLE_FILTER_PANEL':
      return { ...state, filterPanelOpen: !state.filterPanelOpen };
    case 'SET_SELECTED':
      return { ...state, selected: action.ids };
    case 'CLEAR_FILTERS':
      return { ...state, movies: { actor: '', tags: [], rating: 0, status: '', search: '', sort: 'time' } };
    case 'SET_LOADING':
      return { ...state, loading: action.loading };
    default:
      return state;
  }
}

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppState must be inside AppProvider');
  return ctx;
}
