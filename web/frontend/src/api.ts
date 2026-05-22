import type { Movie, Actor, TagConfig, Stats, StatsDetail } from './types';

const BASE = '/api';

async function fetchJSON<T>(url: string, opts?: RequestInit): Promise<T> {
  const resp = await fetch(url, opts);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

async function postJSON<T>(url: string, body: unknown): Promise<T> {
  return fetchJSON<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// Actors
export async function fetchActors(): Promise<Actor[]> {
  return fetchJSON<Actor[]>(`${BASE}/actors`);
}

// Movies
export async function fetchMovies(params: Record<string, string>): Promise<Movie[]> {
  const qs = new URLSearchParams(params).toString();
  return fetchJSON<Movie[]>(`${BASE}/movies?${qs}`);
}

export async function updateMovie(id: string, data: Partial<Pick<Movie, 'rating' | 'tags'>>): Promise<void> {
  await fetch(`${BASE}/movies/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function exportMoviesCSV(params: Record<string, string>): Promise<Blob> {
  const qs = new URLSearchParams(params).toString();
  const resp = await fetch(`${BASE}/movies/export?${qs}`);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.blob();
}

export async function openFolder(movieId: string): Promise<void> {
  await postJSON(`${BASE}/open-folder`, { movie_id: movieId });
}

export async function openFiltered(movieIds: string[]): Promise<void> {
  await postJSON(`${BASE}/open-filtered`, { movie_ids: movieIds });
}

export async function playMovie(movieId: string): Promise<void> {
  await postJSON(`${BASE}/play/${movieId}`, {});
}

// Batch operations
export async function deleteMovies(ids: string[]): Promise<void> {
  await postJSON(`${BASE}/movies/batch/delete`, { movie_ids: ids });
}

export async function moveMovies(ids: string[], dest: string): Promise<void> {
  await postJSON(`${BASE}/movies/batch/move`, { movie_ids: ids, destination: dest });
}

export async function copyMovies(ids: string[], dest: string): Promise<void> {
  await postJSON(`${BASE}/movies/batch/copy`, { movie_ids: ids, destination: dest });
}

export async function batchAddTags(ids: string[], tags: string[]): Promise<void> {
  await postJSON(`${BASE}/movies/batch/tags/add`, { movie_ids: ids, tags });
}

export async function batchSetTags(ids: string[], tags: string[]): Promise<void> {
  await postJSON(`${BASE}/movies/batch/tags/set`, { movie_ids: ids, tags });
}

export async function batchRemoveTags(ids: string[], tags: string[]): Promise<void> {
  await postJSON(`${BASE}/movies/batch/tags/remove`, { movie_ids: ids, tags });
}

// Tags
export async function fetchTags(): Promise<TagConfig> {
  return fetchJSON<TagConfig>(`${BASE}/tags`);
}

export async function addTag(name: string, group: string): Promise<void> {
  await postJSON(`${BASE}/tags/add`, { name, group });
}

export async function renameTag(oldName: string, newName: string): Promise<void> {
  await fetch(`${BASE}/tags/${encodeURIComponent(oldName)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_name: newName }),
  });
}

export async function deleteTag(name: string): Promise<void> {
  await fetch(`${BASE}/tags/${encodeURIComponent(name)}`, { method: 'DELETE' });
}

export async function fetchTagTemplates(): Promise<Record<string, string[]>> {
  return fetchJSON<Record<string, string[]>>(`${BASE}/tag-templates`);
}

// Stats
export async function fetchStats(): Promise<Stats> {
  return fetchJSON<Stats>(`${BASE}/stats`);
}
