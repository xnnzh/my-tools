#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-29 14:35:55
# alias: gitlab-merge-request
# ----------------------------------------------------------------------------------------------------------------------
# 提交Gitlab合并请求
# -----------------------------------------------------------------------------------------------------------------------

set -eo pipefail

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
# 当前分支
CURRENT_BRANCH=$(git_current_branch)
# 远程仓库地址
REMOTE_URL=$(git_remote_url)
# 合并请求的源分支，默认是当前分支
SOURCE_BRANCH="${CURRENT_BRANCH}"
# 合并请求的目标地址
TARGET_BRANCH=""

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <option>

提交Gitlab合并请求。

OPTIONS:
  [--remote-url    | -r] 远程仓库地址
  [--source-branch | -s] 合并请求的源分支
  [--target-branch | -t] 合并请求的目标地址
  [--help          | -h] 帮助
EOF

  exit
}

# 解析参数
while true; do
  if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    helpu
  elif [ "$1" = "--remote-url" ] || [ "$1" = "-r" ]; then
    REMOTE_URL="${2}"
    shift 2
  elif [ "$1" = "--source-branch" ] || [ "$1" = "-s" ]; then
    SOURCE_BRANCH="${2}"
    shift 2
  elif [ "$1" = "--target-branch" ] || [ "$1" = "-t" ]; then
    TARGET_BRANCH="${2}"
    shift 2
  elif [ "$1" = "--browser" ]; then
    BROWSER="${2}"
    shift 2
  else
    break
  fi
done

if [ "X${REMOTE_URL}" = "X" ] || [ "X${SOURCE_BRANCH}" = "X" ] || [ "X${TARGET_BRANCH}" = "X" ]; then
  HOME_URL="$(git_remote_url)"
  # open_url "${HOME_URL%.git*}/-/merge_requests"
  if [ "X${BROWSER}" = "X" ]; then
    open_url "${HOME_URL%.git*}/merge_requests"
  else
    $BROWSER "${HOME_URL%.git*}/merge_requests"
  fi
  helpu
fi

# 执行逻辑

notice_msg "提交Gitlab合并请求"
echo "    当前分支    : ${CURRENT_BRANCH}"
echo "    远程仓库地址: ${REMOTE_URL}"
echo "    源分支      : ${SOURCE_BRANCH}"
echo "    目标分支    : ${TARGET_BRANCH}"

echo " "
# 根据仓库修改
# MERGE_URL="${REMOTE_URL%.git*}/-/merge_requests/new?merge_request%5Bsource_branch%5D=${SOURCE_BRANCH}&merge_request%5Btarget_branch%5D=${TARGET_BRANCH}"
MERGE_URL="${REMOTE_URL%.git*}/merge_requests/new?merge_request%5Bsource_branch%5D=${SOURCE_BRANCH}&merge_request%5Btarget_branch%5D=${TARGET_BRANCH}"
echo "创建合并请求：${MERGE_URL}"

  if [ "X${BROWSER}" = "X" ]; then
    open_url "${MERGE_URL}"
  else
    $BROWSER "${MERGE_URL}"
  fi

notice_msg "完成!"
