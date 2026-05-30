// movie_id is SHA1 hash of file_path
export interface Movie {
  movie_id: string;
  file_name: string;
  movie_name: string;
  actor: string;
  release_year: number;
  rating: number;        // 0-5, 0 = unrated
  file_size: string;     // e.g. "6.27 GB"
  file_path: string;     // absolute path
  status: 'new' | 'classified';
  tags: string;          // comma-separated
  downloaded_at: string; // ISO date
}

export interface Actor {
  name: string;
  count: number;
}

export interface TagConfig {
  available_tags: string[];
  type_tags: string[];
  allow_custom: boolean;
  delimiter: string;
  tag_templates: Record<string, string[]>;
  usage: Record<string, number>;
  custom_tags?: string[];
}

export interface Stats {
  total: number;
  actors_count: number;
  classified: number;
  rated: number;
  tagged: number;
}

export interface StatsDetail {
  total: number;
  classified: number;
  unclassified: number;
  rated: number;
  tagged: number;
  top_actors: Actor[];
  rating_distribution: Record<number, number>;
  tag_counts: Record<string, number>;
  total_size: string;
  avg_rating: number;
  recent_downloads: number;
  duplicate_count: number;
}

export interface PaginatedMovies {
  movies: Movie[];
  total: number;
  page: number;
  per_page: number;
}

export interface PathCheckResult {
  movie_id: string;
  movie_name: string;
  actor: string;
  file_size: string;
  file_path: string;
  exists: boolean;
}

export interface ValidateResponse {
  success: boolean;
  total: number;
  valid: number;
  invalid: number;
  results: PathCheckResult[];
}

export interface RepairResponse {
  success: boolean;
  found: boolean;
  movie_id: string;
  movie_name?: string;
  old_path?: string;
  new_path?: string;
  message?: string;
}

export type SortField = 'time' | 'rating' | 'name';
export type ViewMode = 'card' | 'table';

export interface MovieFilters {
  actor: string;
  tags: string[];
  rating: number;      // minimum rating
  status: string;
  search: string;
  sort: SortField;
  sizeMin: number | null;  // minimum file size in GB
  sizeMax: number | null;  // maximum file size in GB
  dateFrom: string;        // YYYY-MM-DD
  dateTo: string;          // YYYY-MM-DD
}
