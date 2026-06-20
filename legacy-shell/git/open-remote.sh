#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-11-13 17:51:22
# alias: git-open-remote
# ----------------------------------------------------------------------------------------------------------------------
# 在浏览器打开仓库远程地址
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
# 远程仓库地址
REMOTE_URL=$(git_remote_url)

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <option>

在浏览器打开仓库远程地址。

OPTIONS:
  [--help | -h] 帮助
EOF

  exit
}

notice_msg "Remote URL: ${REMOTE_URL%.git*}"

open_url "${REMOTE_URL%.git*}"
