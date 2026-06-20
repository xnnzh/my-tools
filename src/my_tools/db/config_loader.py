import os
import re
from typing import Any

import pyjson5


def _output_fields(entry: dict) -> set[str]:
    fields = {entry['pk']}
    for c in entry.get('collect', []):
        fields.add(c)
    if not entry.get('root'):
        for v in entry.get('via', []):
            fields.add(v['col'])
    return fields


def _resolve_env(value: Any, strict: bool = True) -> Any:
    if isinstance(value, str):
        def replacer(m: re.Match) -> str:
            var = m.group(1)
            val = os.environ.get(var)
            if val is None:
                if strict:
                    raise ValueError(f"环境变量 {var!r} 未设置")
                return m.group(0)
            return val
        return re.sub(r'\$\{(\w+)\}', replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v, strict=strict) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v, strict=strict) for v in value]
    return value


def load_config(path: str, strict: bool = True) -> dict:
    with open(path, encoding='utf-8') as f:
        raw = pyjson5.load(f)
    config = _resolve_env(raw, strict=strict)
    _validate(config)
    return config


def _validate(config: dict):
    conn = config.get('connection')
    if not isinstance(conn, dict):
        raise ValueError("缺少 connection 配置")
    for field in ('host', 'port', 'user', 'password', 'database'):
        if field not in conn:
            raise ValueError(f"connection 缺少字段: {field}")

    tasks = config.get('tasks')
    if not isinstance(tasks, list) or len(tasks) == 0:
        raise ValueError("tasks 至少需要定义一个任务")

    defaults = config.get('defaults', {})
    for task in tasks:
        _validate_task(task, defaults)


def _validate_task(task: dict, defaults: dict):
    if 'name' not in task:
        raise ValueError("每个 task 必须包含 name")
    task.setdefault('batch_size', defaults.get('batch_size', 1000))
    task.setdefault('delete_chunk_size', defaults.get('delete_chunk_size', 500))
    task.setdefault('sleep_seconds', defaults.get('sleep_seconds', 0))

    root = task.get('root')
    if not isinstance(root, dict):
        raise ValueError(f"task [{task['name']}] 缺少 root 配置")
    for field in ('table', 'pk', 'filter'):
        if field not in root:
            raise ValueError(f"task [{task['name']}] root 缺少字段: {field}")

    cascade = task.get('cascade')
    if not isinstance(cascade, list) or len(cascade) == 0:
        raise ValueError(f"task [{task['name']}] cascade 不能为空")

    root_entries = [e for e in cascade if e.get('root')]
    if len(root_entries) != 1:
        raise ValueError(f"task [{task['name']}] cascade 必须有且仅有一个 root: true 的条目")
    root_entry = root_entries[0]
    all_tables = {e['table'] for e in cascade}

    for entry in cascade:
        if 'table' not in entry:
            raise ValueError(f"task [{task['name']}] cascade 条目缺少 table")
        if 'via' not in entry or not isinstance(entry['via'], list) or len(entry['via']) == 0:
            raise ValueError(f"task [{task['name']}] cascade.{entry['table']} 缺少 via")
        if 'pk' not in entry:
            raise ValueError(f"task [{task['name']}] cascade.{entry['table']} 缺少 pk")
        if entry.get('root'):
            if 'collect' not in entry:
                raise ValueError(f"task [{task['name']}] cascade.{entry['table']} (root) 必须包含 collect 字段")
        else:
            if 'parent' not in entry:
                raise ValueError(f"task [{task['name']}] cascade.{entry['table']} 非根条目缺少 parent")
            if entry['parent'] not in all_tables:
                raise ValueError(
                    f"task [{task['name']}] cascade.{entry['table']}"
                    f" 的 parent {entry['parent']} 不在 cascade 中"
                )

    names_seen = set()
    for entry in cascade:
        t = entry['table']
        if t in names_seen:
            raise ValueError(f"task [{task['name']}] cascade 中存在重复表: {t}")
        names_seen.add(t)

    if root_entry['table'] != root['table']:
        raise ValueError(
            f"task [{task['name']}] root 表 {root['table']} 与 cascade root 表 {root_entry['table']} 不一致"
        )

    table_map = {e['table']: e for e in cascade}

    for entry in cascade:
        if entry.get('root'):
            continue
        parent_entry = table_map.get(entry['parent'])
        if parent_entry is None:
            continue
        parent_out = _output_fields(parent_entry)
        for v in entry['via']:
            if v['ref'] not in parent_out:
                raise ValueError(
                    f"task [{task['name']}] cascade.{entry['table']}"
                    f" via.ref={v['ref']!r} 在父表 {parent_entry['table']} 的输出中不存在"
                    f"（父表输出字段: {sorted(parent_out)}）"
                )

    parent_map = {e['table']: e.get('parent') for e in cascade if not e.get('root')}
    visited = {root_entry['table']}
    stack = [root_entry['table']]
    while stack:
        cur = stack.pop()
        children = [t for t, p in parent_map.items() if p == cur and t not in visited]
        visited.update(children)
        stack.extend(children)
    isolated = all_tables - visited
    if isolated:
        raise ValueError(
            f"task [{task['name']}] cascade 中存在孤立表（无法从 root 连通）: {', '.join(sorted(isolated))}"
        )
