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
  top_actors: Actor[];
  rating_distribution: Record<number, number>;
  tag_counts: Record<string, number>;
  total_size: string;
  avg_rating: number;
  recent_downloads: number;
  duplicate_count: number;
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
}
