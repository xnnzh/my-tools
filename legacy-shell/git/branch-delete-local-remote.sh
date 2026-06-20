#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-19 21:06:00
# alias: git-delete-branch
# ----------------------------------------------------------------------------------------------------------------------
# 脚本执行逻辑：
#     1. 删除指定的本地分支；
#     2. 如果本地分支与远程分支有关联，则也会删除对应的远程分支；
#     3. 如果本地分支与远程分支没有关联，并且远程存在同名分支，也会删除同名的远程分支；
#     4. 如果指定的分支在本地不存在，并且远程存在同名分支，也会删除同名的远程分支。
# ----------------------------------------------------------------------------------------------------------------------

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

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <option>

删除指定的本地分支和对应的远程分支。

OPTIONS:
  [-b         ] [branchName ...] 指定分支名，多个用空格隔开 
  [--help | -h]                  帮助
EOF

  exit
}

# 解析参数
while true; do
  if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    helpu
  elif [ "$1" = "-b" ]; then
    shift 1
  else
    break
  fi
done

if [ "X${*}" = "X" ]; then
  helpu
fi

# 执行逻辑

git fetch

idxl=0
idxr=0

for b in ${*}; do
  if git show-ref --quiet refs/heads/${b}; then
    LOCAL_BRANCH[${idxl}]="${b}"
    idxl=$((idxl + 1))

    # 对应的远程分支
    CURRENT_REMOTE_BRANCH=$(git_remote_branch "${b}")
    if [ "X${CURRENT_REMOTE_BRANCH}" != "X" ]; then
      REMOTE_BRANCH[${idxr}]="${CURRENT_REMOTE_BRANCH#origin/}"
      idxr=$((idxr + 1))
    elif git_check_branch_in_remote "$b"; then
      REMOTE_BRANCH[${idxr}]="$b"
      idxr=$((idxr + 1))
    fi
  elif git_check_branch_in_remote "$b"; then
    REMOTE_BRANCH[${idxr}]="$b"
    idxr=$((idxr + 1))
  fi
done

if [ "X${LOCAL_BRANCH[*]}" != "X" ]; then
  notice_msg "删除本地分支: git branch -D ${LOCAL_BRANCH[*]}"
  git branch -D "${LOCAL_BRANCH[@]}"
fi

if [ "X${REMOTE_BRANCH[*]}" != "X" ]; then
  notice_msg "删除远程分支: git push origin --delete ${REMOTE_BRANCH[*]}"
  git push origin --delete "${REMOTE_BRANCH[@]}"
fi

notice_msg "完成!"
