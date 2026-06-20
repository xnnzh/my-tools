#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-22 16:51:12
# alias: mvn-simple
# ----------------------------------------------------------------------------------------------------------------------
# 执行maven命令时，跳过单元测试，跳过生成JavaDoc文档，跳过SpringBoot等。
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
. "${APP_HOME}/utils/common.sh"

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <maven command>

执行maven命令时，跳过单元测试，跳过生成JavaDoc文档。

OPTIONS:
  [--help | -h]    帮助
EOF

  exit
}

# 解析参数

if [ ${#} -eq 0 ]; then
  helpu
fi

# 执行逻辑

notice_msg "开始执行Maven命令: mvn ${*} -DskipTests=true -Dmaven.javadoc.skip=true -Dmaven.springboot.skip=true"

mvn "${@}" -DskipTests=true -Dmaven.javadoc.skip=true -Dmaven.springboot.skip=true

notice_msg "完成!"
