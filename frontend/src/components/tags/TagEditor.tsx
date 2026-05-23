// TagEditor is embedded in MovieCard component via Popover.
// This file provides a more reusable version if needed later.

import { useState } from 'react';
import { Tag, Input, Button, Space, Divider } from 'antd';
import { useStore } from '../../store';

interface TagEditorProps {
  currentTags: string[];
  onToggle: (tag: string) => void;
  onAddCustom: (name: string) => Promise<void>;
}

export function TagEditor({ currentTags, onToggle, onAddCustom }: TagEditorProps) {
  const tagsConfig = useStore((s) => s.tagsConfig);
  const [input, setInput] = useState('');
  const tagConfig = tagsConfig;

  if (!tagConfig) return null;

  const allTags = [
    ...tagConfig.available_tags,
    ...tagConfig.type_tags,
    ...(tagConfig.custom_tags || []),
  ];

  return (
    <div style={{ width: 280 }}>
      <div style={{ marginBottom: 8, fontSize: 12, color: '#88889a' }}>
        当前标签: {currentTags.length > 0 ? currentTags.join(', ') : '无'}
      </div>
      <Space wrap size={[4, 4]} style={{ marginBottom: 12 }}>
        {allTags
          .filter((t) => !currentTags.includes(t))
          .map((t) => (
            <Tag key={t} style={{ cursor: 'pointer' }} onClick={() => onToggle(t)}>
              + {t}
            </Tag>
          ))}
      </Space>
      {tagConfig.allow_custom && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <Input
            size="small"
            placeholder="自定义标签"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={() => onAddCustom(input).then(() => setInput(''))}
            suffix={
              <Button
                size="small"
                type="link"
                onClick={() => onAddCustom(input).then(() => setInput(''))}
              >
                添加
              </Button>
            }
          />
        </>
      )}
    </div>
  );
}
