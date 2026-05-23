"""Tag management routes."""

import json

from flask import Blueprint, jsonify, request

from web.server_state import get_state
from web.shared import (
    CONFIG_PATH,
    _has_traditional,
    _JAPANESE_RE,
    _load_config,
    get_actress_names,
    get_available_tags,
    get_excel,
    get_tag_config,
)

tags_bp = Blueprint('tags', __name__)


def _clean_custom_tags(tags_usage: dict, actress_names: set[str]) -> list:
    """Filter custom tags: exclude actress names, Japanese, and traditional Chinese."""
    clean = []
    for tag in tags_usage:
        if tag in actress_names:
            continue
        if _JAPANESE_RE.search(tag):
            continue
        if _has_traditional(tag):
            continue
        clean.append(tag)
    clean.sort(key=lambda t: -tags_usage[t])
    return clean


@tags_bp.route('/api/tag-templates')
def api_tag_templates():
    return jsonify(get_tag_config().get('tag_templates', {}))


@tags_bp.route('/api/tags')
def api_tags():
    excel = get_excel()
    state = get_state()
    state.ensure_fresh(excel)

    available = get_available_tags()
    type_tags = get_tag_config().get('type_tags', [])
    all_defined = set(available + type_tags)
    custom_keys = set(state.tags_usage.keys()) - all_defined
    custom_tags = sorted(custom_keys, key=lambda t: -state.tags_usage[t])
    if custom_tags:
        actress_names = get_actress_names(excel)
        custom_tags = _clean_custom_tags(
            {t: state.tags_usage[t] for t in custom_tags},
            actress_names,
        )
    delimiter = get_tag_config().get('delimiter', ',')

    return jsonify({
        'available_tags': available,
        'type_tags': type_tags,
        'custom_tags': custom_tags,
        'usage': state.tags_usage,
        'allow_custom': get_tag_config().get('allow_custom', True),
        'delimiter': delimiter,
    })


@tags_bp.route('/api/tags/add', methods=['POST'])
def add_tag():
    data = request.get_json() or {}
    new_tag = data.get('tag', '').strip()
    group = data.get('group', 'attribute')
    if not new_tag:
        return jsonify({'success': False, 'error': '标签名不能为空'}), 400

    key = 'type_tags' if group == 'type' else 'available_tags'
    group_cn = '类型' if group == 'type' else '属性'
    config = _load_config()
    tag_list = config.setdefault('tag_config', {}).get(key, [])
    if new_tag in tag_list:
        return jsonify({'success': False, 'error': f'标签「{new_tag}」已在{group_cn}组中'}), 409

    other_key = 'available_tags' if group == 'type' else 'type_tags'
    other_list = config['tag_config'].get(other_key, [])
    if new_tag in other_list:
        other_cn = '属性' if group == 'type' else '类型'
        return jsonify({'success': False, 'error': f'标签「{new_tag}」已在{other_cn}组中，请先在另一组删除再添加'}), 409

    tag_list.append(new_tag)
    config['tag_config'][key] = tag_list
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'tag': new_tag, 'group': group})


@tags_bp.route('/api/tags/<tagname>', methods=['DELETE'])
def delete_tag(tagname):
    data = request.get_json() or {}
    clean_movies = data.get('clean_movies', False)

    config = _load_config()
    tc = config.setdefault('tag_config', {})
    for key in ('available_tags', 'type_tags'):
        lst = tc.get(key, [])
        if tagname in lst:
            lst.remove(tagname)
            tc[key] = lst
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            cleaned = 0
            if clean_movies:
                excel = get_excel()
                tags_idx = excel._get_column_index('tags')
                for r in excel.get_all_movies():
                    tags_str = r.get('tags', '')
                    current = [t.strip() for t in tags_str.split(',') if t.strip()]
                    if tagname in current:
                        current.remove(tagname)
                        row = excel.find_row_by_id(r['movie_id'])
                        if row:
                            row[tags_idx].value = ','.join(current)
                            cleaned += 1
                excel.save()

            get_state().invalidate()
            return jsonify({'success': True, 'removed': tagname, 'cleaned_movies': cleaned})

    return jsonify({'success': False, 'error': '标签不存在'}), 404


@tags_bp.route('/api/tags/<tagname>', methods=['PUT'])
def rename_tag(tagname):
    data = request.get_json() or {}
    new_name = (data.get('new_name', '') or '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': '新标签名不能为空'}), 400

    config = _load_config()
    tc = config.setdefault('tag_config', {})

    for key in ('available_tags', 'type_tags'):
        lst = tc.get(key, [])
        if tagname in lst:
            if new_name in lst:
                return jsonify({'success': False, 'error': '新标签名已存在'}), 409
            idx = lst.index(tagname)
            lst[idx] = new_name
            tc[key] = lst
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            excel = get_excel()
            tags_idx = excel._get_column_index('tags')
            updated = 0
            for r in excel.get_all_movies():
                tags_str = r.get('tags', '')
                current = [t.strip() for t in tags_str.split(',') if t.strip()]
                if tagname in current:
                    current[current.index(tagname)] = new_name
                    row = excel.find_row_by_id(r['movie_id'])
                    if row:
                        row[tags_idx].value = ','.join(current)
                        updated += 1
            excel.save()

            get_state().invalidate()
            return jsonify({'success': True, 'old': tagname, 'new': new_name, 'updated_movies': updated})

    return jsonify({'success': False, 'error': '原标签不存在'}), 404
