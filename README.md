# My-Tools

个人命令行工具集，基于 Python + uv，统一入口为 `my-tools`。

`legacy-shell/` 中保留历史 Shell 实现，仅作为参考。

## 安装

```shell
git clone https://github.com/xnnzh/my-tools

cd my-tools

uv sync
uv run my-tools install
```

当 `uv tool install . --force` 因缓存未拾取最新源码修复时，使用强制重装：

```shell
uv run my-tools install --force-reinstall
```

安装后：

```shell
my-tools --help
```

## 开发运行

```shell
uv run my-tools --help
uv run my-tools list
uv run ruff check .
uv run pytest
```

## 命令列表

```shell
my-tools install
my-tools install --force-reinstall
my-tools uninstall
my-tools update
my-tools update --force-reinstall
my-tools list

my-tools git auto
my-tools git new-branch
my-tools git delete-branch
my-tools git open-remote
my-tools git gitlab-merge-request
my-tools git copy-change

my-tools file new-with-template
my-tools file zip

my-tools maven simple

my-tools db batch-delete

my-tools completion show --shell zsh
my-tools completion install --shell zsh
```

## DB 工具

`my-tools db batch-delete` 按配置的条件批量删除 MySQL 表数据，支持 keyset 分页、级联收集、事务内分 chunk 删除。

```shell
# 列出配置文件中的所有任务
my-tools db batch-delete configs/clean_hsdi.jsonc --list

DB_USER=root DB_PASS=xxx \
  my-tools db batch-delete configs/clean_hsdi.jsonc --task clean_hsdi_interface --dry-run

my-tools db batch-delete configs/clean_hsdi.jsonc --env .env --task clean_hsdi_interface
```

- `.env` 不提交
- `.env.example` 可复制
- 日志 `app-{PID}.log` 已忽略

## my-ssh

my-ssh 暂未提供 Python 版；历史 Shell 实现在 `legacy-shell/net/my-ssh.sh`。

## License

[MIT License](https://opensource.org/licenses/MIT)
