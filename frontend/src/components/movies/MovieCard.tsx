import { Checkbox, Tag, Rate, Popover, Button, Input, Space, Divider, message, Tooltip } from 'antd';
import { FolderOpenOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { Movie } from '../../types';
import { useStore } from '../../store';
import { updateMovie, addTag, openFolder, playMovie } from '../../api';
import { useRating } from '../../hooks/useRating';

interface MovieCardProps {
  movie: Movie;
  onUpdated: () => void;
}

export function MovieCard({ movie, onUpdated }: MovieCardProps) {
  const selected = useStore((s) => s.selected);
  const setSelected = useStore((s) => s.setSelected);
  const tagsConfig = useStore((s) => s.tagsConfig);
  const [editing, setEditing] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const { handleRatingChange } = useRating({ onUpdated });

  const tagConfig = tagsConfig;
  const allTags = tagConfig
    ? [...tagConfig.available_tags, ...tagConfig.type_tags, ...(tagConfig.custom_tags || [])]
    : [];
  const currentTags = movie.tags ? movie.tags.split(',').map((t) => t.trim()).filter(Boolean) : [];

  const isSelected = selected.has(movie.movie_id);
  const ratingClass = movie.rating >= 4 ? 'rated-high' : movie.rating > 0 ? 'rated' : '';

  const toggleSelect = () => {
    const next = new Set(selected);
    if (isSelected) next.delete(movie.movie_id);
    else next.add(movie.movie_id);
    setSelected(next);
  };

  const handleTagToggle = async (tag: string) => {
    const newTags = currentTags.includes(tag)
      ? currentTags.filter((t) => t !== tag)
      : [...currentTags, tag];
    try {
      await updateMovie(movie.movie_id, { tags: newTags.join(',') });
      message.success('标签已更新');
      onUpdated();
    } catch {
      message.error('标签更新失败');
    }
  };

  const handleAddCustomTag = async () => {
    const name = tagInput.trim();
    if (!name) return;
    try {
      if (!allTags.includes(name) && tagConfig?.allow_custom) {
        await addTag(name, 'type');
      }
      const newTags = [...currentTags, name];
      await updateMovie(movie.movie_id, { tags: newTags.join(',') });
      message.success('标签已添加');
      setTagInput('');
      setEditing(false);
      onUpdated();
    } catch {
      message.error('操作失败');
    }
  };

  const [imgSrc, setImgSrc] = useState(`/api/cover/${movie.movie_id}`);
  const [imgHidden, setImgHidden] = useState(false);

  const handleImgError = () => {
    setImgHidden(true);
  };

  return (
    <div className={`movie-card ${ratingClass} ${isSelected ? 'selected' : ''}`}>
      {/* Cover image */}
      <div className="card-thumb" onClick={() => playMovie(movie.movie_id)} title="点击播放">
        {!imgHidden && (
          <img
            src={imgSrc}
            alt={movie.movie_name || movie.file_name}
            loading="lazy"
            onError={handleImgError}
          />
        )}
        <PlayCircleOutlined className="card-thumb-play" />
      </div>
      <div className="card-body">
        <div className="card-header">
          <Checkbox checked={isSelected} onChange={toggleSelect} />
        <span className="card-code" onClick={() => playMovie(movie.movie_id)} title="点击播放">
          {movie.movie_name || movie.file_name}
        </span>
        <Tooltip title="在资源管理器中打开">
          <FolderOpenOutlined
            style={{ color: '#88889a', cursor: 'pointer', fontSize: 14 }}
            onClick={() => openFolder(movie.movie_id)}
          />
        </Tooltip>
      </div>
      <div style={{ color: '#88889a', fontSize: 13, marginBottom: 4 }}>
        {movie.actor || '未知演员'} · {movie.release_year || '未知年份'}
      </div>
      <div className="card-meta">
        <Rate value={movie.rating} onChange={(v) => handleRatingChange(movie.movie_id, v)} style={{ fontSize: 16 }} />
        <span>{movie.file_size}</span>
      </div>
      <div className="card-tags">
        {currentTags.map((t) => (
          <Tag key={t} closable onClose={() => handleTagToggle(t)} color="default">
            {t}
          </Tag>
        ))}
        <Popover
          open={editing}
          onOpenChange={setEditing}
          trigger="click"
          content={
            <div style={{ width: 260 }}>
              <div style={{ marginBottom: 8, fontSize: 12, color: '#88889a' }}>选择标签</div>
              <Space wrap size={[4, 4]}>
                {allTags
                  .filter((t) => !currentTags.includes(t))
                  .map((t) => (
                    <Tag
                      key={t}
                      style={{ cursor: 'pointer' }}
                      onClick={() => {
                        handleTagToggle(t);
                        setEditing(false);
                      }}
                    >
                      + {t}
                    </Tag>
                  ))}
              </Space>
              {tagConfig?.allow_custom && (
                <>
                  <Divider style={{ margin: '10px 0' }} />
                  <Input
                    size="small"
                    placeholder="自定义标签"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onPressEnter={handleAddCustomTag}
                    suffix={
                      <Button size="small" type="link" onClick={handleAddCustomTag}>
                        添加
                      </Button>
                    }
                  />
                </>
              )}
            </div>
          }
        >
          <span className="tag-add">+</span>
        </Popover>
      </div>
      </div> {/* card-body */}
    </div>
  );
}
