import { Checkbox, Tag, Rate, Popover, Button, Input, Space, Divider, message, Tooltip } from 'antd';
import { PlusOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { Movie } from '../../types';
import { useAppState } from '../../context/AppContext';
import { updateMovie, addTag, openFolder, playMovie } from '../../api';

interface MovieCardProps {
  movie: Movie;
  onUpdated: () => void;
}

export function MovieCard({ movie, onUpdated }: MovieCardProps) {
  const { state, dispatch } = useAppState();
  const [editing, setEditing] = useState(false);
  const [tagInput, setTagInput] = useState('');

  const tagConfig = state.tagsConfig;
  const allTags = tagConfig
    ? [...tagConfig.available_tags, ...tagConfig.type_tags, ...(tagConfig.custom_tags || [])]
    : [];
  const currentTags = movie.tags ? movie.tags.split(',').map((t) => t.trim()).filter(Boolean) : [];

  const isSelected = state.selected.has(movie.movie_id);
  const ratingClass = movie.rating >= 4 ? 'rated-high' : movie.rating > 0 ? 'rated' : '';

  const toggleSelect = () => {
    const next = new Set(state.selected);
    if (isSelected) next.delete(movie.movie_id);
    else next.add(movie.movie_id);
    dispatch({ type: 'SET_SELECTED', ids: next });
  };

  const handleTagToggle = async (tag: string) => {
    const newTags = currentTags.includes(tag)
      ? currentTags.filter((t) => t !== tag)
      : [...currentTags, tag];
    try {
      await updateMovie(movie.movie_id, { tags: newTags.join(',') });
      message.success('标签已更新');
      onUpdated();
    } catch (e) {
      message.error('标签更新失败');
    }
  };

  const handleAddCustomTag = async () => {
    const name = tagInput.trim();
    if (!name) return;
    try {
      // Add to library if custom
      if (!allTags.includes(name) && tagConfig?.allow_custom) {
        await addTag(name, 'type');
      }
      const newTags = [...currentTags, name];
      await updateMovie(movie.movie_id, { tags: newTags.join(',') });
      message.success('标签已添加');
      setTagInput('');
      setEditing(false);
      onUpdated();
    } catch (e) {
      message.error('操作失败');
    }
  };

  const handleRatingChange = async (v: number) => {
    try {
      await updateMovie(movie.movie_id, { rating: v });
      message.success('评分已保存');
      onUpdated();
    } catch (e) {
      message.error('评分保存失败');
    }
  };

  return (
    <div className={`movie-card ${ratingClass} ${isSelected ? 'selected' : ''}`}>
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
        <Rate value={movie.rating} onChange={handleRatingChange} style={{ fontSize: 16 }} />
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
    </div>
  );
}
