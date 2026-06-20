import os
import sys

from dotenv import load_dotenv

from .config_loader import load_config
from .task_runner import Log, TaskRunner


def _print_task_summary(task: dict, tasks: list[dict]):
    root = task['root']
    cascade = task['cascade']
    lines = [
        f'╔══ Task: {task["name"]} ══╗',
        f'║ DB:   {task.get("_db", "-")}',
        '╠══════════════════════════',
        f'║ Root:      {root["table"]}',
        f'║ PK:        {root["pk"]}',
        f'║ Filter:    {root["filter"]}',
        f'║ Batch:     {task["batch_size"]}',
        f'║ Chunk:     {task["delete_chunk_size"]}',
        f'║ Sleep:     {task["sleep_seconds"]}s',
        '╠══════════════════════════',
        '║ Cascade (自底向上删除):',
    ]
    for i, entry in enumerate(cascade, 1):
        via_str = ', '.join(v['col'] for v in entry['via'])
        marker = ' (根)' if entry.get('root') else ''
        lines.append(f'║  {i}. {entry["table"]}{marker}')
        lines.append(f'║     → WHERE ({via_str}) IN (...)')
    lines.append('╚══════════════════════════')
    for line in lines:
        print(line)
        Log.log(line)


def run_interactive(config: dict, *, dry_run: bool = False):
    import questionary

    tasks = config['tasks']
    conn_info = f"{config['connection']['host']}:{config['connection']['port']}/{config['connection']['database']}"

    choices = []
    for t in tasks:
        label = f'{t["name"]}  [{t["root"]["table"]}] {t.get("desc", "")}'
        choices.append(questionary.Choice(title=label, value=t))

    selected = questionary.checkbox(
        '选择要执行的任务（空格选中/取消，回车确认）:',
        choices=choices,
    ).ask()

    if not selected:
        print('未选择任何任务，退出')
        return

    for t in selected:
        t['_db'] = conn_info
        _print_task_summary(t, tasks)

    summary = ', '.join(t['name'] for t in selected)
    Log.log(f'待执行任务: {summary}')
    if dry_run:
        Log.log('模式: DRY-RUN（仅统计，不删除）')

    confirm = questionary.confirm('继续执行?', default=False).ask()
    if not confirm:
        Log.log('已取消')
        return

    run_tasks(config, selected, dry_run=dry_run)


def run_tasks(config: dict, selected_tasks: list[dict], *, dry_run: bool = False):
    conn_config = config['connection']
    for task in selected_tasks:
        Log.log('')
        runner = TaskRunner(conn_config, task, dry_run=dry_run)
        runner.run()


def run_batch_delete(
    config_path: str,
    tasks: tuple[str, ...] = (),
    list_tasks: bool = False,
    dry_run: bool = False,
    env_file: str | None = None,
    log_file: str | None = None,
    no_log_file: bool = False,
):
    if env_file:
        load_dotenv(env_file)

    if no_log_file:
        log_path = None
    elif log_file:
        log_path = log_file
    else:
        log_path = f'./app-{os.getpid()}.log'
    Log.open(log_path)

    try:
        config = load_config(config_path, strict=not list_tasks)

        if list_tasks:
            print(f'配置文件: {config_path}')
            print(f'共 {len(config["tasks"])} 个任务:\n')
            for t in config['tasks']:
                cascade_count = len(t['cascade'])
                print(f'  {t["name"]}')
                print(f'    描述:   {t.get("desc", "-")}')
                print(f'    根表:   {t["root"]["table"]}')
                print(f'    Filter: {t["root"]["filter"]}')
                print(f'    层级:   {cascade_count} 张表')
                print()
            return

        conn_info = f"{config['connection']['host']}:{config['connection']['port']}/{config['connection']['database']}"

        if tasks:
            task_names = set(tasks)
            selected = [t for t in config['tasks'] if t['name'] in task_names]
            missing = task_names - {t['name'] for t in config['tasks']}
            if missing:
                print(f'任务不存在: {", ".join(missing)}')
                sys.exit(1)
            for t in selected:
                t['_db'] = conn_info
                _print_task_summary(t, config['tasks'])

            Log.log(f'待执行任务: {", ".join(t["name"] for t in selected)}')
            if dry_run:
                Log.log('模式: DRY-RUN（仅统计，不删除）')

            import questionary
            confirm = questionary.confirm('继续执行?', default=False).ask()
            if not confirm:
                Log.log('已取消')
                return

            run_tasks(config, selected, dry_run=dry_run)
        else:
            run_interactive(config, dry_run=dry_run)
    finally:
        Log.close()
