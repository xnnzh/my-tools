import time
from datetime import datetime
from typing import Any

import pymysql
from pymysql.cursors import DictCursor


class Log:
    _file = None

    @classmethod
    def open(cls, path: str | None):
        if path:
            cls._file = open(path, 'a', encoding='utf-8')

    @classmethod
    def close(cls):
        if cls._file:
            cls._file.close()
            cls._file = None

    @classmethod
    def log(cls, msg: str):
        line = f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}'
        print(line)
        if cls._file:
            cls._file.write(line + '\n')
            cls._file.flush()


def _plural(n: int) -> str:
    return '条' if n <= 1 else '条'


def _build_in_values(rows: list[dict], via: list[dict]) -> tuple[str, list]:
    field_count = len(via)
    col_names = ', '.join(v['col'] for v in via)
    params = []
    for row in rows:
        for v in via:
            params.append(row[v['ref']])
    if field_count == 1:
        placeholders = ','.join(['%s'] * len(rows))
        sql = f'{col_names} IN ({placeholders})'
    else:
        placeholders = ','.join([f'({",".join(["%s"] * field_count)})' for _ in range(len(rows))])
        sql = f'({col_names}) IN ({placeholders})'
    return sql, params


def _via_values_repr(rows: list[dict], via: list[dict], limit: int = 20) -> str:
    parts = []
    for row in rows:
        vals = [str(row[v['ref']]) for v in via]
        parts.append(f'({", ".join(vals)})' if len(vals) > 1 else vals[0])
    preview = ', '.join(parts)
    if len(parts) > limit:
        preview = ', '.join(parts[:limit]) + f', ... (共 {len(parts)} 个)'
    return preview


def _pk_values_repr(rows: list[dict], pk: str, limit: int = 20) -> str:
    vals = [str(row[pk]) for row in rows]
    preview = ', '.join(vals)
    if len(vals) > limit:
        preview = ', '.join(vals[:limit]) + f', ... (共 {len(vals)} 个)'
    return preview


def _format_sql(sql: str, params: list) -> str:
    result = []
    param_iter = iter(params)
    for part in sql.split('%s'):
        result.append(part)
        try:
            val = next(param_iter)
        except StopIteration:
            continue
        if isinstance(val, str):
            escaped = val.replace("'", "''").replace('\\', '\\\\')
            result.append(f"'{escaped}'")
        elif isinstance(val, (int, float)):
            result.append(str(val))
        elif val is None:
            result.append('NULL')
        else:
            result.append(str(val))
    return ''.join(result)


class TaskRunner:
    def __init__(self, conn_config: dict, task: dict, *, dry_run: bool = False):
        self.conn_config = conn_config
        self.task = task
        self.dry_run = dry_run
        self.root = task['root']
        self.batch_size = task['batch_size']
        self.chunk_size = task['delete_chunk_size']
        self.sleep_seconds = task['sleep_seconds']
        self.cascade = self._topological_sort(task['cascade'])
        self.root_entry = next(e for e in self.cascade if e.get('root'))

    @staticmethod
    def _topological_sort(cascade: list[dict]) -> list[dict]:
        table_map = {e['table']: e for e in cascade}
        depth: dict[str, int] = {}

        def compute_depth(entry: dict) -> int:
            t = entry['table']
            if t in depth:
                return depth[t]
            if entry.get('root'):
                depth[t] = 0
                return 0
            parent = entry.get('parent')
            if parent and parent in table_map:
                depth[t] = compute_depth(table_map[parent]) + 1
            else:
                depth[t] = 0
            return depth[t]

        for entry in cascade:
            compute_depth(entry)

        return sorted(cascade, key=lambda e: depth.get(e['table'], 0))

    def _get_connection(self) -> pymysql.Connection:
        return pymysql.connect(
            host=self.conn_config['host'],
            port=int(self.conn_config['port']),
            user=self.conn_config['user'],
            password=self.conn_config['password'],
            database=self.conn_config['database'],
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=False,
        )

    def _print_sql_templates(self):
        print('  [收集 SQL 模板]:')
        print(f'    {self.root["table"]}: SELECT {self.root["pk"]}, {", ".join(self.root_entry.get("collect", []))} '
              f'FROM {self.root["table"]} WHERE {self.root["filter"]} '
              f'AND {self.root["pk"]} > :last_pk ORDER BY {self.root["pk"]} LIMIT {self.batch_size}')

        for entry in self.cascade:
            if entry.get('root'):
                continue
            via_str = ', '.join(f'{v["col"]}(ref:{v["ref"]})' for v in entry['via'])
            print(f'    {entry["table"]}: SELECT pk... '
                  f'FROM {entry["table"]} WHERE ({via_str}) IN (:parent_values)')

        print('  [删除 SQL 模板]:')
        for entry in reversed(self.cascade):
            pk_col = entry.get('pk') or '<pk>'
            print(f'    {entry["table"]}: DELETE FROM {entry["table"]} WHERE {pk_col} IN (:values)')

    def _collect_root_batch(self, cursor, last_pk: Any | None) -> tuple[list[dict], Any | None]:
        pk = self.root['pk']
        collect_fields = self.root_entry.get('collect', [])
        all_cols = [pk] + [c for c in collect_fields if c != pk]
        select_cols = ', '.join(all_cols)

        if last_pk is None:
            sql = (
                f'SELECT {select_cols} FROM {self.root["table"]}'
                f' WHERE {self.root["filter"]} ORDER BY {pk} LIMIT %s'
            )
            params = (self.batch_size,)
        else:
            sql = (
                f'SELECT {select_cols} FROM {self.root["table"]}'
                f' WHERE {self.root["filter"]} AND {pk} > %s ORDER BY {pk} LIMIT %s'
            )
            params = (last_pk, self.batch_size)
        Log.log(f'  收集 SQL: {_format_sql(sql, list(params))}')
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            return [], None

        max_pk = max(row[pk] for row in rows)
        return rows, max_pk

    def _collect_child(self, cursor, entry: dict, parent_rows: list[dict]) -> list[dict]:
        via = entry['via']
        in_sql, params = _build_in_values(parent_rows, via)

        pk = entry.get('pk')
        collect_fields = entry.get('collect', [])

        sel_parts = list(collect_fields)
        if pk and pk not in sel_parts:
            sel_parts.append(pk)
        for v in via:
            col = v['col']
            if col not in sel_parts:
                sel_parts.append(col)
        select_cols = ', '.join(sel_parts) if sel_parts else '*'

        sql = f'SELECT {select_cols} FROM {entry["table"]} WHERE {in_sql}'
        Log.log(f'  收集 SQL: {_format_sql(sql, params)}')
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        vals_repr = _via_values_repr(parent_rows, via)
        Log.log(f'  收集: {entry["table"]} → 共 {len(rows)}{_plural(len(rows))}  IN: {vals_repr}')
        return rows

    def _get_parent_rows(self, entry: dict, all_data: dict[str, list]) -> list[dict]:
        parent_table = entry.get('parent')
        if parent_table is None:
            return []
        return all_data.get(parent_table, [])

    def _delete_table(self, cursor, entry: dict, rows: list[dict]):
        if not rows:
            Log.log(f'  删除: {entry["table"]} → 无需删除')
            return

        pk = entry.get('pk') or entry['via'][0]['col']
        vals = [row[pk] for row in rows]

        for i in range(0, len(vals), self.chunk_size):
            chunk = vals[i:i + self.chunk_size]
            chunk_num = i // self.chunk_size + 1
            total_chunks = (len(vals) + self.chunk_size - 1) // self.chunk_size

            placeholders = ','.join(['%s'] * len(chunk))
            template = f'DELETE FROM {entry["table"]} WHERE {pk} IN ({placeholders})'
            full_sql = _format_sql(template, chunk)
            Log.log(f'  删除: {entry["table"]} → chunk {chunk_num}/{total_chunks} ({len(chunk)}{_plural(len(chunk))})')
            Log.log(f'    SQL: {full_sql}')
            cursor.execute(template, chunk)

    def run(self):
        task_name = self.task['name']
        Log.log(f'Task [{task_name}] — 开始执行')

        self._print_sql_templates()

        pk = self.root['pk']
        last_pk: Any | None = None
        batch_num = 0
        total_stats: dict[str, int] = {}
        task_start = time.time()

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                while True:
                    root_rows, max_pk = self._collect_root_batch(cursor, last_pk)
                    if not root_rows:
                        break

                    batch_num += 1
                    Log.log(f'─── Batch {batch_num} start (last_{pk}={last_pk}) ───')

                    root_vals_repr = _via_values_repr(root_rows, self.root_entry['via'])
                    Log.log(
                        f'  收集: {self.root["table"]} → 共 {len(root_rows)}{_plural(len(root_rows))}'
                        f' ({pk}: {root_rows[0][pk]} ~ {root_rows[-1][pk]})'
                    )
                    Log.log(f'    IN: {root_vals_repr}')

                    all_data: dict[str, list] = {self.root['table']: root_rows}
                    for entry in self.cascade:
                        if entry.get('root'):
                            continue
                        parent_rows = self._get_parent_rows(entry, all_data)
                        if not parent_rows:
                            all_data[entry['table']] = []
                            continue
                        child_rows = self._collect_child(cursor, entry, parent_rows)
                        all_data[entry['table']] = child_rows

                    if self.dry_run:
                        Log.log('  [DRY-RUN] 跳过删除')
                        for entry in reversed(self.cascade):
                            d = all_data.get(entry['table'], [])
                            Log.log(f'  [DRY-RUN] 将删除 {entry["table"]}: {len(d)}{_plural(len(d))}')
                    else:
                        Log.log(f'─── 删除 batch {batch_num} (事务中) ───')
                        try:
                            cursor.execute('BEGIN')
                            batch_stats: dict[str, int] = {}
                            for entry in reversed(self.cascade):
                                rows = all_data.get(entry['table'], [])
                                self._delete_table(cursor, entry, rows)
                                batch_stats[entry['table']] = len(rows)

                            cursor.execute('COMMIT')
                            stats_str = ', '.join(f'{k}:{v}' for k, v in batch_stats.items())
                            Log.log('COMMIT')
                            Log.log(f'✔ Batch {batch_num} 完成: 删除汇总 [{stats_str}]')

                            for k, v in batch_stats.items():
                                total_stats[k] = total_stats.get(k, 0) + v
                        except Exception:
                            cursor.execute('ROLLBACK')
                            Log.log(f'✘ Batch {batch_num} 失败，已回滚')
                            raise

                    last_pk = max_pk
                    if self.sleep_seconds > 0:
                        time.sleep(self.sleep_seconds)

        finally:
            conn.close()

        elapsed = time.time() - task_start
        if not self.dry_run:
            total_str = ', '.join(f'{k}:{v}' for k, v in total_stats.items())
            Log.log(f'✔ Task [{task_name}] 完成')
            Log.log(f'  总计: 批次 {batch_num}, 删除行数 [{total_str}]')
        else:
            Log.log(f'✔ Task [{task_name}] Dry-Run 完成')
            Log.log(f'  总计: 扫描 batch {batch_num}')
        Log.log(f'  耗时: {elapsed:.1f}s')
