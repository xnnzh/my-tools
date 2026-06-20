#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-19 21:30:00
# ----------------------------------------------------------------------------------------------------------------------
# 通用模块，提供通用的功能
# ----------------------------------------------------------------------------------------------------------------------

# ~ 定义变量
# ----------------------------------------------------------------------------------------------------------------------

# Colors
# 参考: https://gist.github.com/jonsuh/3c89c004888dfc7352be
NOCOLOR='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
LIGHTGRAY='\033[0;37m'
DARKGRAY='\033[1;30m'
LIGHTRED='\033[1;31m'
LIGHTGREEN='\033[1;32m'
YELLOW='\033[1;33m'
LIGHTBLUE='\033[1;34m'
LIGHTPURPLE='\033[1;35m'
LIGHTCYAN='\033[1;36m'
WHITE='\033[1;37m'

# ~ 通用函数
# ----------------------------------------------------------------------------------------------------------------------

# 输出提示信息
notice_msg() {
  echo -e "${GREEN}${*}${NOCOLOR}"
}

# 输出错误信息
error_msg() {
  echo -e "${RED}${*}${NOCOLOR}"
  echo " "
  exit
}

echo_orange() {
  echo -e "${ORANGE}${*}${NOCOLOR}"
}

# 询问是否继续的函数
confirm_go_on() {
  while true; do
    read -r -p "$(echo -e "${ORANGE}${*-"是否继续"}?(y/n)${NOCOLOR}")" yn
    case ${yn} in
    # 默认什么都不输入是Y
    [Yy]* | "") ;;
    [Nn]*) exit ;;
    *) echo "请输入y/n" ;;
    esac
  done
}

# 询问是否继续的函数
confirm_go_on_v2() {
  local flag
  while true; do
    read -r -p "$(echo -e "${ORANGE}${*-"是否继续"}?(y/n)${NOCOLOR}")" yn
    case ${yn} in
    # 默认什么都不输入是Y
    [Yy]* | "")
      flag="Y"
      break
      ;;
    [Nn]*)
      flag="N"
      break
      ;;
    esac
  done
  echo "${flag}"
}

# ~ 系统相关函数
# ----------------------------------------------------------------------------------------------------------------------

# 获取系统名称
# 参考: https://stackoverflow.com/a/27776822/6003235
get_os_name() {
  case "$(uname -s)" in
  Darwin) echo 'Mac' ;;
  Linux) echo 'Linux' ;;
  CYGWIN* | MINGW32* | MSYS* | MINGW*) echo 'Windows' ;;
  *) echo 'Other' ;;
  esac
}

# 在浏览器打开url
# $1 要打开的url
# 参考：https://stackoverflow.com/a/38147878/6003235
open_url() {
  case "$(get_os_name)" in
  Mac) open "$@" ;;
  Linux)
    if command -v xdgpen >/dev/null; then
      xdgpen "$@"
    else
      echo "xdgpen命令不存在, 请手动在浏览器打开："
      echo "$@"
    fi
    ;;
  Windows) start "$@" ;;
  Other)
    echo "未能识别的系统, 请手动在浏览器打开："
    echo "${*}"
    ;;
  esac
}

# 结束指定的进程
# $1 pid
# $2 超时时间，默认为10秒
kill_by_pid() {
  pid=$1
  count=$2
  n=0

  if [ "x${count}" = "x" ]; then
    count=10
  fi

  while [ $n -lt $count ]; do
    n=$((n + 1))

    # 判断进程是否结束
    kill -0 ${pid}
    if [ $? -ne 0 ]; then
      echo "Success!"
      break
    else
      if [ $n -ne 0 ]; then
        sleep 1
      fi
      if [ $n -eq ${count} ]; then
        kill -9 ${pid}
      else
        kill -15 ${pid}
      fi
    fi
  done
}

# Git相关函数
# ----------------------------------------------------------------------------------------------------------------------

# 当前Git分支
git_current_branch() {
  git symbolic-ref --short -q HEAD
}

# 获取远程仓库的url
git_remote_url() {
  git config -l | awk -F 'remote.origin.url=' '/remote\.origin\.url=/ {print $2}'
}

# 获取本地分支对应的远程分支
git_remote_branch() {
  if [ "X${*}" = "X" ]; then
    # 适用于当前分支
    git for-each-ref --format='%(upstream:short)' "$(git symbolic-ref -q HEAD)"
  else
    # 使用于任何分支
    if git rev-parse --abbrev-ref --symbolic-full-name "${*}"@{u} >/dev/null 2>&1; then
      git rev-parse --abbrev-ref --symbolic-full-name "${*}"@{u}
    fi
  fi
}

# 判断远程是否存在分支
git_check_branch_in_remote() {
  if [ "X${*}" = "X" ]; then
    git_check_branch_in_remote "$(git_current_branch)"
  elif git ls-remote --exit-code --heads origin "${*}" >/dev/null 2>&1; then
    true
  else
    false
  fi
}

# 文件相关函数
# ----------------------------------------------------------------------------------------------------------------------

# 询问是否删除文件的函数
delete_file() {
  local flag="Y"
  if [ -f "$1" ]; then
    if [ "$2" = "true" ]; then
      rm -f "$1"
      flag="Y"
    else
      while true; do
        read -p "${4-是否要删除}${1}?(y/n)" yn
        case ${yn} in
        [Yy]*)
          rm -f "$1"
          flag="Y"
          break
          ;;
        [Nn]*)
          if [ "$3" = "true" ]; then
            exit
          else
            flag="N"
            break
          fi
          ;;
        esac
      done
    fi
  else
    flag="N"
  fi
  echo "${flag}"
}
