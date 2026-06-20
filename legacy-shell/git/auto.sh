#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-21 16:00:00
# alias: git-auto
# ----------------------------------------------------------------------------------------------------------------------
# git status ==> git add . ==> git commit ==> git pull --rebase ==> git push
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
# commit信息
COMMIT_MSG=()
# 默认的commit信息
DEFAULT_COMMIT_MSG="Update changes $(date '+%Y-%m-%d %H:%M:%S')"
LOOP_INDEX=0

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 [option]

提交当前分支的变更，并推送到远程。

OPTIONS:
  [-m         ] <commitMessage>  指定提交信息
  [--help | -h]                  帮助
EOF

  exit
}

# 解析参数
while true; do
  if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    helpu
  elif [ "$1" = "-m" ]; then
    COMMIT_MSG[$((LOOP_INDEX++))]="${1}"
    COMMIT_MSG[$((LOOP_INDEX++))]="${2}"
    shift 2
  else
    break
  fi
done

# 执行逻辑

echo ""
notice_msg "Time: $(date '+%Y-%m-%d %H:%M:%S')"
notice_msg "User: $(git config user.name)"
notice_msg "Email: $(git config user.email)"
notice_msg "Remote: $(git remote get-url origin)"
echo ""

echo_orange "git fetch"
git fetch origin --prune
echo ""

# 当前分支
CURRENT_BRANCH=$(git_current_branch)
# 远程分支
REMOTE_BRANCH=$(git_remote_branch)

notice_msg "Current branch: ${CURRENT_BRANCH} ==> ${REMOTE_BRANCH:-[no remote branch]}"

echo_orange "git status"
git status

change_count=$(git status --porcelain | awk 'END{print NR}')
stash_count=$(git stash list | wc -l)
change_stash=""

if [ "${change_count}" != "0" ]; then
  # Add changes to git
  if [ "$(confirm_go_on_v2 "git add .")" = "Y" ]; then
    git add .
    # Commit changes
    if [ "$(confirm_go_on_v2 "git commit")" = "Y" ]; then
      if [ ${#COMMIT_MSG[@]} -eq 0 ]; then
        COMMIT_MSG[$((LOOP_INDEX++))]="-m"
        while true; do
          read -p "请输入提交信息(不输入将使用默认提交信息): " msg
          if [ "X${msg}" = "X" ]; then
            COMMIT_MSG[$((LOOP_INDEX++))]="${DEFAULT_COMMIT_MSG}"
            break
          else
            COMMIT_MSG[$((LOOP_INDEX++))]="${msg}"
            break
          fi
        done
      fi
      git commit "${COMMIT_MSG[@]}"
    else
      notice_msg "Completed!"
      exit
    fi
  else
    change_stash="stash"
  fi
fi

# 没有对应的远程分支
if [ "X${REMOTE_BRANCH}" = "X" ]; then
  notice_msg "Completed!"
  exit
fi

# git stash
if [ "X${change_stash}" = "Xstash" ]; then
  git stash
fi

# 落后远程分支的提交数
behind_count=$(git rev-list --count HEAD..@{u})
if [ "${behind_count}" != "0" ]; then
  echo_orange "git pull --rebase"
  git pull --rebase
fi

# 领先远程分支的提交数
ahead_count=$(git rev-list --count @{u}..HEAD)
if [ "${ahead_count}" != "0" ]; then
  echo_orange "git push"
  git push
fi

# git unstash
if [ "X${change_stash}" = "Xstash" ] && [ "${stash_count}" != "$(git stash list | wc -l)" ]; then
  git stash pop
fi

notice_msg "Completed!"
