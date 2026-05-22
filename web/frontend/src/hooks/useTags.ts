import { useEffect } from 'react';
import { useAppState } from '../context/AppContext';
import * as api from '../api';

import React from 'react';

export function useTags() {
  const { state, dispatch } = useAppState();

  useEffect(() => {
    api.fetchTags().then((config) => {
      dispatch({ type: 'SET_TAGS_CONFIG', config });
    });
    api.fetchStats().then((stats) => {
      dispatch({ type: 'SET_STATS', stats });
    });
  }, [dispatch]);

  const activeFilterCount =
    (state.movies.rating > 0 ? 1 : 0) +
    (state.movies.status ? 1 : 0) +
    state.movies.tags.length;

  const allTags = state.tagsConfig
    ? [...state.tagsConfig.available_tags, ...state.tagsConfig.type_tags, ...(state.tagsConfig.custom_tags || [])]
    : [];

  return { activeFilterCount, allTags };
}
