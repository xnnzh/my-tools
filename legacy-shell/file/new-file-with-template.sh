#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-22 16:07:00
# alias: file-new-with-template
# ----------------------------------------------------------------------------------------------------------------------
# 根据模板文件生成新文件
# ----------------------------------------------------------------------------------------------------------------------

set -eo pipefail

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
# 模板文件，有默认值
TEMPLATE_FILE_PATH="${APP_HOME}/.run/file-template"
# 生成的目标文件
TARGET_FILE_PATH=""
# 是否强制覆盖已存在的文件
FORCE_FLAG=false

# 定义函数
# 帮助函数
helpu() {
    cat <<EOF

usage: $0 [option] <file-path ...>

根据模板文件生成新文件。

OPTIONS:
  [--template | -t] [template-file-path] 指定模板文件路径
  [--force    | -f]                      强制覆盖已存在的文件
  [--help     | -h]                      帮助
EOF

    exit
}

# 解析参数
while true; do
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        helpu
    elif [ "$1" = "--template" ] || [ "$1" = "-t" ]; then
        TEMPLATE_FILE_PATH="${2}"
        shift 2
    elif [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
        FORCE_FLAG=true
        shift 1
    else
        break
    fi
done

TARGET_FILE_PATH=("${@}")

if [ ${#TARGET_FILE_PATH[@]} -eq 0 ]; then
    helpu
fi

# 执行逻辑

notice_msg "1)解析模板文件 ${TEMPLATE_FILE_PATH}"
if [ ! -f "${TEMPLATE_FILE_PATH}" ]; then
    error_msg "模板文件不存在 ${TEMPLATE_FILE_PATH}"
fi

notice_msg "2)生成文件:"

for file_path in ${TARGET_FILE_PATH[*]}; do
    delete_file "${file_path}" "${FORCE_FLAG}" "true"

    sed -e "s {{NOW_TIME}} $(date '+%Y-%m-%d\ %H:%M:%S') g" \
        "${TEMPLATE_FILE_PATH}" >"${file_path}"

    echo "    ${file_path}"
done

notice_msg "完成!"
