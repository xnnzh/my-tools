#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2021-10-18 19:18:03
# alias: my-ssh
# reference: https://github.com/MFrank2016/GotoSSH
# ----------------------------------------------------------------------------------------------------------------------
# ssh工具
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
. "${APP_HOME}/utils/common.sh"

# 定义变量
# 运行的临时脚本
RUN_FILE="${APP_HOME}/.run/my-ssh-run"
# 配置文件
CONFIG_FILE="${APP_HOME}/.run/.my-ssh-config"
# 配置文件内容
CONFIG_CONTENT=""
# 服务器的数量
SERVER_COUNT=0
# 当前服务器命令列表
COMMAND_LIST=""
# 当前服务器命令的个数
COMMAND_COUNT=0

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 [option] <command>

ssh工具。

OPTIONS:
  [-l] 查看服务器列表
  [--help     | -h] 帮助
EOF

  exit
}

echo_title() {
  notice_msg "------------------------- $1 -------------------------"
}

echo_server_line() {
  echo_orange "$1 >" "$(echo "$2" | sed 's/||/ /g' | awk '{ printf "%s(%s)", $7, $2 }')"
}

echo_server_list() {
  echo_title "服务器列表"
  for serverLine in ${CONFIG_CONTENT}; do
    if [[ "${serverLine}" == *\[Server* ]]; then
      break
    fi
    echo_server_line "$((++SERVER_COUNT))" "${serverLine}"
  done
}

echo_command_line() {
  echo_orange "$1 >> $2"
}

echo_command_list() {
  local tmpServerConfig=$1
  local commandList
  local commonCommandList
  commandList=$(sed -n "/\[${tmpServerConfig}\]/,/^\[/p" "${CONFIG_FILE}" | sed '/^\[.*\]/d' | awk -F '=' '{print $1}' | sed '/^$/d')
  commonCommandList=$(sed -n '/\[common-command\]/,/^\[/p' "${CONFIG_FILE}" | sed '/^\[.*\]/d' | awk -F '=' '{print $1}' | sed '/^$/d')
  if [ -n "${commandList}" ] || [ -n "${commonCommandList}" ]; then
    echo_title "命令列表"
    COMMAND_LIST=$(echo -e "不执行命令\n${commandList}\n${commonCommandList}" | sed '/^$/d')
    for tmp in ${COMMAND_LIST}; do
      echo_command_line $((++COMMAND_COUNT)) "${tmp}"
    done
  fi
}

get_command() {
  local tmp_section="Server-$1"
  local tmp_command=$2
  local tmp_commandInfo
  tmp_commandInfo=$(get_config_line "${tmp_section}" "${tmp_command}")
  if [ -z "${tmp_commandInfo}" ]; then
    # 如果自定义命令中未读取到该命令，则前往模板命令中读取
    tmp_commandInfo=$(get_config_line "common-command" "${tmp_command}")
  fi
  echo "${tmp_commandInfo}"
}

get_config_line() {
  local tmp_section=$1
  local tmp_key=$2
  local tmp_config_line
  tmp_config_line=$(sed -n "/\[${tmp_section}\]/,/^\[/p" "${CONFIG_FILE}" | grep "^${tmp_key}=" | sed "s#${tmp_key}=##")
  echo "${tmp_config_line}"
}

insert_server_info() {
  local tmpServerConfig=$1
  local tmpIp
  local tmpName
  local tmpPwd
  local tmpPort
  local tmpRely
  local publicKeyPath=""
  local tmpRelies=()
  local tmpLoop=0
  local tmpLoopRely
  tmpRely=$(echo "${tmpServerConfig}" | sed 's/||/ /g' | awk '{ print $6 }')
  tmpLoopRely=${tmpRely}

  while [ "${tmpLoopRely}x" != "0x" ]; do
    tmpRelies[$tmpLoop]=$(sed -n "/^${tmpLoopRely}||/p" "${CONFIG_FILE}")
    if [ "${tmpRelies[$tmpLoop]}x" = "x" ]; then
      error_msg "未找到服务器信息: ${tmpRelies[$tmpLoop]}"
      exit
    fi
    tmpLoopRely=$(echo "${tmpRelies[$tmpLoop]}" | sed 's/||/ /g' | awk '{ print $6 }')
    ((tmpLoop++))
  done

  local index=$((tmpLoop - 1))
  while [ ${index} -ge 0 ]; do
    tmpIp=$(echo "${tmpRelies[${index}]}" | sed 's/||/ /g' | awk '{ print $2 }')
    tmpName=$(echo "${tmpRelies[${index}]}" | sed 's/||/ /g' | awk '{ print $3 }')
    tmpPwd=$(echo "${tmpRelies[${index}]}" | sed 's/||/ /g' | awk '{ print $4 }')
    tmpPort=$(echo "${tmpRelies[${index}]}" | sed 's/||/ /g' | awk '{ print $5 }')

    if [[ ${tmpPwd} == file://* ]]; then
      publicKeyPath=" -i ${tmpPwd#*file://}"
    fi

    if [ "${tmpPort}x" = "x" ]; then
      tmpPort=22
    fi

    if [ ${index} = $((tmpLoop - 1)) ]; then
      printf '%s\r' "spawn ssh${publicKeyPath} -p${tmpPort} -l ${tmpName} ${tmpIp}" >>"${RUN_FILE}"
    else
      printf '%s\r' "send \"ssh${publicKeyPath} -p${tmpPort} -l ${tmpName} ${tmpIp}\r\"" >>"${RUN_FILE}"
    fi

    if [[ ${tmpPwd} != file://* ]]; then
      cat >>"${RUN_FILE}" <<EOF
expect {
    "*yes/no" { send "yes\r"; exp_continue }
    "*password*" { send "${tmpPwd}\r" }
}
EOF
    fi

    # echo 'expect "*]*"' >> "${RUN_FILE}"
    printf '%s\r' "expect -re \$RE_PROMPT" >>"${RUN_FILE}"

    ((index--))
  done

  tmpIp=$(echo "${tmpServerConfig}" | sed 's/||/ /g' | awk '{ print $2 }')
  tmpName=$(echo "${tmpServerConfig}" | sed 's/||/ /g' | awk '{ print $3 }')
  tmpPwd=$(echo "${tmpServerConfig}" | sed 's/||/ /g' | awk '{ print $4 }')
  tmpPort=$(echo "${tmpServerConfig}" | sed 's/||/ /g' | awk '{ print $5 }')

  if [[ ${tmpPwd} == file://* ]]; then
    publicKeyPath=" -i ${tmpPwd#*file://}"
  fi

  if [ -z "${tmpPort}" ]; then
    tmpPort=22
  fi

  if [ "${tmpRely}" != "0" ]; then
    printf '%s\r' "send \"ssh${publicKeyPath} -p${tmpPort} -l ${tmpName} ${tmpIp}\r\"" >>"${RUN_FILE}"
  else
    printf '%s\r' "spawn ssh${publicKeyPath} -p${tmpPort} -l ${tmpName} ${tmpIp}" >>"${RUN_FILE}"
  fi

  if [[ ${tmpPwd} != file://* ]]; then
    cat >>"${RUN_FILE}" <<EOF
expect {
    "*yes/no" { send "yes\r"; exp_continue }
    "*password*" { send "${tmpPwd}\r" }
}
EOF
  fi
}

# 执行逻辑

# 若临时脚本文件不存在则创建
if [ ! -f "${RUN_FILE}" ]; then
  touch "${RUN_FILE}"
fi
echo "" >"${RUN_FILE}"

# 判断配置文件是否存在
if [ ! -f "${CONFIG_FILE}" ]; then
  error_msg "${CONFIG_FILE} 配置文件不存在"
  exit
fi
CONFIG_CONTENT="$(cat "${CONFIG_FILE}")"

# -l 命令
if [ "${1}" == "-l" ]; then
  echo_server_list
  exit
fi

# 读取选择的服务器
if [ -n "${1}" ]; then
  NO=${1}
else
  NO=0
  echo_server_list
  until [ "${NO}x" != "x" ] && [ ${NO} -gt 0 ] && [ ${NO} -le "${SERVER_COUNT}" ]; do
    echo -e 'Server Number:\c'
    read -r NO
  done
fi

# 读取该服务器配置
SERVER_LINE_INFO=$(sed -n "${NO}p" "${CONFIG_FILE}")
if [ -z "${SERVER_LINE_INFO}" ]; then
  error_msg "未找到服务器信息: ${NO}"
  exit
fi

SERVER_LINK_NAME=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk '{ print $1 }')
# SERVER_IP=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk  '{ print $2 }')
# LOGIN_NAME=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk  '{ print $3 }')
# LOGIN_PWD=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk  '{ print $4 }')
# SSH_PORT=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk  '{ print $5 }')
# SERVER_RELY=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk  '{ print $6 }')
# SERVICE_NAME=$(echo "${SERVER_LINE_INFO}" | sed 's/||/ /g' | awk  '{ print $7 }')
SERVER_CONFIG_NAME="Server-${SERVER_LINK_NAME}"

# -cl 命令-输出该服务器的自定义命令列表
if [ "${2}" == "-cl" ]; then
  echo_command_list "${SERVER_CONFIG_NAME}"
  exit
fi

cat >"${RUN_FILE}" <<EOF
#!/usr/bin/expect -f
set timeout 30

set RE_PROMPT "(#|>|\\\\$|❯ )"
EOF

# 下载
if [ "${2}" == "down" ] && [ "${3}x" != "x" ] && [ "${4}x" != "x" ]; then
  insert_down_info "${SERVER_LINE_INFO}" "${3}" "${4}"
  chmod a+x "${RUN_FILE}"
  ${RUN_FILE}
  # echo '' > "${RUN_FILE}"
  exit
fi

# 上传
if [ "${2}" == "up" ] && [ "${3}x" != "x" ] && [ "${4}x" != "x" ]; then
  insert_up_info "${SERVER_LINE_INFO}" "${3}" "${4}"
  chmod a+x "${RUN_FILE}"
  ${RUN_FILE}
  echo '' >"${RUN_FILE}"
  exit
fi

insert_server_info "${SERVER_LINE_INFO}"

# 读取命令参数
if [ -n "${2}" ]; then
  COMMAND=$(get_command "${SERVER_LINK_NAME}" "${2}")
else
  echo_command_list "${SERVER_CONFIG_NAME}"
  if [ "${COMMAND_LIST}x" = "x" ]; then
    COMMAND=""
  else
    tmpCommandNumber=0
    until [ "${tmpCommandNumber}x" != "x" ] && [ "${tmpCommandNumber}" -gt 0 ] && [ "${tmpCommandNumber}" -le "${COMMAND_COUNT}" ]; do
      echo -e 'Command Number:\c'
      read -r tmpCommandNumber
    done
    if [ "${tmpCommandNumber}" -eq "1" ]; then
      COMMAND=""
    else
      COMMAND=$(echo "${COMMAND_LIST}" | sed -n "${tmpCommandNumber}p")
      COMMAND=$(get_command "${SERVER_LINK_NAME}" "${COMMAND}")
    fi
  fi
fi

# 处理命令中的密码
if [[ ${COMMAND} == *\|* ]]; then
  COMMAND_PWD=$(echo "${COMMAND}" | awk -F\| '{ print $2 }')
  COMMAND="${COMMAND%%|*}"
fi

# 命令及命令的密码
if [ -n "${COMMAND}" ]; then
  printf '%s\r' "expect -re \$RE_PROMPT" >>"${RUN_FILE}"
  printf '%s\r' "send  \"${COMMAND}\r\"" >>"${RUN_FILE}"
fi
if [ -n "${COMMAND_PWD}" ]; then
  echo 'expect "*password:"' >>"${RUN_FILE}"
  printf '%s\r' "send  \"${COMMAND_PWD}\r\"" >>"${RUN_FILE}"
fi

echo 'interact' >>"${RUN_FILE}"
chmod a+x "${RUN_FILE}"
"${RUN_FILE}"
echo '' >"${RUN_FILE}"
