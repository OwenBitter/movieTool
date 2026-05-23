import { useEffect } from 'react';
import { useStore } from '../store';
import * as api from '../api';

export function useTags() {
  const movies = useStore((s) => s.movies);
  const tagsConfig = useStore((s) => s.tagsConfig);
  const setTagsConfig = useStore((s) => s.setTagsConfig);
  const setStats = useStore((s) => s.setStats);

  useEffect(() => {
    api.fetchTags().then(setTagsConfig);
    api.fetchStats().then(setStats);
  }, [setTagsConfig, setStats]);

  const activeFilterCount =
    (movies.rating > 0 ? 1 : 0) +
    (movies.status ? 1 : 0) +
    movies.tags.length;

  const allTags = tagsConfig
    ? [...tagsConfig.available_tags, ...tagsConfig.type_tags, ...(tagsConfig.custom_tags || [])]
    : [];

  return { activeFilterCount, allTags };
}
