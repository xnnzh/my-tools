#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-09-30 17:25:05
# alias: myzip
# ----------------------------------------------------------------------------------------------------------------------
# 压缩文件，解决Mac中的zip压缩包在其他系统中解压，会多出__MACOSX文件夹和.DS_Store文件的问题。
# ----------------------------------------------------------------------------------------------------------------------

set -e

SCRIPTPATH=$(
  cd "$(dirname "$0")"
  pwd
)

# 根路径
export APP_HOME="${SCRIPTPATH%/my-tools/*}/my-tools"
# 引入通用模块
# shellcheck source=/dev/null
. "${APP_HOME}"/utils/common.sh

# 定义变量
# 生成的目标文件
SOURCE_DIRS=""

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <dir ...>

压缩文件夹，多个用空格隔开。

OPTIONS:
  [--help     | -h]                      帮助
EOF

  exit
}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  helpu
fi

SOURCE_DIRS=("${@}")

if [ ${#SOURCE_DIRS[@]} -eq 0 ]; then
  helpu
fi

# 执行逻辑

for dir in ${SOURCE_DIRS[*]}; do

  if [ ! -d "${dir}" ]; then
    echo "文件不存在 ${dir}"
  else
    if [ ! -f "${dir}.zip" ] || [ "$(delete_file "${dir}.zip" "false" "false" "是否删除已存在的")" = "Y" ]; then
      zip -x "*.DS_Store" -x "__MACOSX" -r "${dir}.zip" "${dir}"
    fi
  fi
done

notice_msg "完成!"
