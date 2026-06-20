#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2023-04-10 10:01:26
# alias: git-copy-change
# ----------------------------------------------------------------------------------------------------------------------
# 复制两次提交之间变更过的文件
# ----------------------------------------------------------------------------------------------------------------------

set -e

SCRIPTPATH=$(
  cd "$(dirname "$0")"
  pwd
)

# 根路径
export APP_HOME="${SCRIPTPATH%/my-tools/*}/my-tools"
# 引入git通用模块
# shellcheck source=/dev/null
. "${APP_HOME}/utils/common.sh"

# 定义变量
# 两次 git 提交的 sha 值
DIFF_SHA1=""
DIFF_SHA2=""
TARGET_DIR=""

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <sha1> <sha2> --target-dir <dir>

复制两次提交之间变更过的文件。

OPTIONS:
  [--target-dir | -t] 复制的目标目录
  [--help       | -h] 帮助
EOF

  exit
}

if [ "$1" = "--help" ] || [ "$1" = "--h" ]; then
  helpu
fi

if [ -z "$1" ] || [ -z "$2" ]; then
  helpu
fi

DIFF_SHA1="$1"
DIFF_SHA2="$2"
shift 2

# 解析参数
while true; do
  if [ "$1" = "--target-dir" ] || [ "$1" = "-t" ]; then
    TARGET_DIR="$2"
    break
  fi
done

if [ "X${TARGET_DIR}" = "X" ]; then
  helpu
fi

git diff --name-only "${DIFF_SHA1}" "${DIFF_SHA2}" | xargs -I{} cp --parents {} "${TARGET_DIR}"
