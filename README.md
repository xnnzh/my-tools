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
my-tools file csv-render
my-tools file json-pretty
my-tools file json-compact
my-tools file json-escape
my-tools file json-unescape

my-tools maven simple

my-tools db batch-delete
my-tools db mybatis-sql
my-tools db insert-sql-to-csv

my-tools time to-timestamp
my-tools time from-timestamp

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

### INSERT SQL 转 CSV

`my-tools db insert-sql-to-csv` 将 `insert into ... values ...` SQL 转换为 CSV，CSV 标题使用 insert 中的列名。

```shell
my-tools db insert-sql-to-csv insert.sql -o result.csv

cat insert.sql | my-tools db insert-sql-to-csv > result.csv
```

输入：

```sql
insert into table1 (id, name, age)
values
  (1, 'Alice', 18),
  (2, 'Bob', 20);
```

输出：

```csv
id,name,age
1,Alice,18
2,Bob,20
```

### MyBatis 日志转 SQL

`my-tools db mybatis-sql` 将 MyBatis 日志中的 `Preparing` / `Parameters` 行转换为可执行的 SQL，支持从 stdin 或文件输入：

```shell
# 从 stdin 管道
cat app.log | my-tools db mybatis-sql

# 从文件
my-tools db mybatis-sql app.log

# 追加模式，保留原日志
my-tools db mybatis-sql app.log --mode append

# 仅输出 SQL
my-tools db mybatis-sql app.log --mode sql-only

# 禁用分号
my-tools db mybatis-sql app.log --no-semicolon

# 严格模式（参数不匹配返回错误）
my-tools db mybatis-sql app.log --strict

# 重定向输出
my-tools db mybatis-sql app.log > output.sql
```

## 文件工具

### CSV 模板渲染

`my-tools file csv-render` 将任意 CSV 按模板渲染为文本，模板变量直接使用 CSV 表头字段名。

```shell
my-tools file csv-render users.csv --format "{name} is {age}"

cat users.csv | my-tools file csv-render --format "{name}: {message}"
```

阿里云日志 CSV 示例：

```shell
my-tools file csv-render aliyun.csv \
  --format "{@timestamp} {level} [{thread_name}] {logger_name} - {message}"

my-tools file csv-render aliyun.csv \
  | my-tools db mybatis-sql --mode append
```

默认模板：

```text
{@timestamp} {level} [{thread_name}] {logger_name} - {message}
```

模板变量直接使用 CSV 原始表头，例如：

```shell
my-tools file csv-render aliyun.csv \
  --format "{@timestamp} [{__tag__:_pod_name_}] {level} {message}"
```

## JSON 处理

### JSON 美化

```shell
my-tools file json-pretty data.json
cat data.json | my-tools file json-pretty
my-tools file json-pretty data.json -o pretty.json
my-tools file json-pretty data.json --indent 4 --sort-keys
```

### JSON 压缩

```shell
my-tools file json-compact data.json
cat data.json | my-tools file json-compact
my-tools file json-compact data.json -o compact.json
```

### JSON 转义

```shell
printf '%s' '{"name":"张三"}' | my-tools file json-escape
printf '%s' '{"name":"张三"}' | my-tools file json-escape --wrap
my-tools file json-escape raw.txt -o escaped.txt
```

### JSON 去除转义

```shell
printf '%s' '{\"name\":\"张三\"}' | my-tools file json-unescape
printf '%s' '"{\"name\":\"张三\"}"' | my-tools file json-unescape
my-tools file json-unescape escaped.txt -o raw.txt
```

默认保留中文；如需转义为 `\uXXXX`，使用 `--ascii`。

## 时间工具

### 日期时间转时间戳

```shell
my-tools time to-timestamp "2026-06-21 12:30:00"

my-tools time to-timestamp "2026-06-21 12:30:00" --unit s

my-tools time to-timestamp "2026-06-21 12:30:00" --timezone UTC
```

### 时间戳转日期时间

```shell
my-tools time from-timestamp 1782016200000

my-tools time from-timestamp 1782016200 --unit s

my-tools time from-timestamp 1782016200000 --timezone UTC

my-tools time from-timestamp 1782016200000 --format "%Y-%m-%dT%H:%M:%S%z"
```

## 命令补全

补全脚本安装后，Click 会自动补全子命令、option 名称和部分动态参数。

当前动态补全包括：

- `my-tools git delete-branch <TAB>`：补全本地 Git 分支

示例：

```shell
my-tools completion install --shell zsh
my-tools git delete-branch fe<TAB>
```

## my-ssh

my-ssh 暂未提供 Python 版；历史 Shell 实现在 `legacy-shell/net/my-ssh.sh`。

## License

[MIT License](https://opensource.org/licenses/MIT)
