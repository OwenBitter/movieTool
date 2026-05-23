import { useStore } from '../store';

export function useTags() {
  const movies = useStore((s) => s.movies);
  const tagsConfig = useStore((s) => s.tagsConfig);

  const activeFilterCount =
    (movies.rating > 0 ? 1 : 0) +
    (movies.status ? 1 : 0) +
    movies.tags.length;

  const allTags = tagsConfig
    ? [...tagsConfig.available_tags, ...tagsConfig.type_tags, ...(tagsConfig.custom_tags || [])]
    : [];

  return { activeFilterCount, allTags };
}
