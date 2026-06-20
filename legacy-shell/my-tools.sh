#!/usr/bin/env bash

# author: xnnzh
# license: MIT
# contact: zhangxinbetter@gmail.com
# website: https://github.com/xnnzh
# time: 2020-08-20 20:30:00
# alias: my-tools
# ----------------------------------------------------------------------------------------------------------------------
# My-Tools管理脚本，用于安装、卸载、更新等操作。
# ----------------------------------------------------------------------------------------------------------------------

set -e

# 应用的目录
APP_HOME=$(
  cd "$(dirname "$0")"
  pwd
)
export APP_HOME=${APP_HOME}

# shellcheck source=/dev/null
. "${APP_HOME}/utils/common.sh"

# 定义变量

# 安装目录
APP_DIST="${APP_HOME}/.run"
# 安装文件
INSTALL_FILE="${APP_DIST}/my-tools"
# 配置忽略安装的文件
IGNORE_FILE="${APP_HOME}/.my-toolsignore"
# 忽略安装的文件
IGNORE_LIST=(".git" "README.md" "CLAUDE.md" ".my-toolsignore" ".gitignore" ".run")
# Python工具目录
PYTHON_TOOL_SCRIPT_HOME="${APP_HOME}/python/tool-script"

# shell的配置文件
SHELL_RC_FILE=("${HOME}/.zshrc" "${HOME}/.bashrc")

# 定义函数
# 帮助函数
helpu() {
  cat <<EOF

usage: $0 <option>

提供便利的命令行工具

OPTIONS:
  [--install   | -i] 安装/重装Shell和Python工具
  [--uninstall | -u] 卸载Shell命令链接，保留Python本地配置
  [--update        ] 拉取仓库更新并重新安装
  [--list      | -l] 列出所有命令
  [--version   | -v] 版本
  [--help      | -h] 帮助
EOF
}

# 提示函数
after_complete() {
  echo " "
  echo "为了正常使用，请重启shell或者执行如下命令(取决于当前使用的shell环境): "
  echo " "
  for rc_file in ${SHELL_RC_FILE[*]}; do
    if [ -f "${rc_file}" ]; then
      echo "    source ${rc_file}"
    fi
  done
  echo " "
}

add_x() {
  if [ -f "${1}" ]; then
    if [ ! -x "${1}" ]; then
      chmod a+x "${1}"
    fi
  fi
}

check_python_tools_prerequisites() {
  if [ ! -d "${PYTHON_TOOL_SCRIPT_HOME}" ]; then
    return 1
  fi

  if ! command -v uv >/dev/null 2>&1; then
    error_msg "未找到uv命令，Python工具需要先安装uv: https://docs.astral.sh/uv/"
  fi
}

install_python_tools() {
  if [ ! -d "${PYTHON_TOOL_SCRIPT_HOME}" ]; then
    return
  fi

  notice_msg "准备安装Python工具 ${PYTHON_TOOL_SCRIPT_HOME}"
  check_python_tools_prerequisites

  (
    cd "${PYTHON_TOOL_SCRIPT_HOME}"
    uv sync
  )

  notice_msg "Python工具安装完成!"
}

uninstall_python_tools() {
  if [ ! -d "${PYTHON_TOOL_SCRIPT_HOME}" ]; then
    return
  fi

  notice_msg "Python工具通过Shell alias暴露，卸载命令链接后即不可直接调用。"
  notice_msg "保留 ${PYTHON_TOOL_SCRIPT_HOME}/.venv 和 .env 等本地文件，如需彻底清理请手动删除。"
}

update_my_tools() {
  notice_msg "准备更新 ${APP_HOME}"

  if git -C "${APP_HOME}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "${APP_HOME}" pull --ff-only
  else
    echo_orange "当前目录不是Git仓库，跳过git pull。"
  fi

  uninstall_my_tools
  install_my_tools
  after_complete
}

# 安装函数
install_my_tools() {
  local idx=${#IGNORE_LIST[@]}

  notice_msg "准备安装 ${APP_HOME}"

  if [ ! -d "${APP_DIST}" ]; then
    mkdir "${APP_DIST}"
    echo "[创建] ${APP_DIST}"
  fi

  if [ -f "${INSTALL_FILE}" ]; then
    rm -f "${INSTALL_FILE}"
  fi

  touch "${INSTALL_FILE}"
  echo "[创建] ${INSTALL_FILE}"

  # 读取要忽略的文件
  if [ -f "${IGNORE_FILE}" ]; then
    # || [ -n "$line" ] 防止文件最后一行不是空行时，不能被读到的问题
    while IFS= read -r line || [ -n "$line" ]; do
      # 去掉#开头的注释和空行
      if [ "${line%${line#?}}"x != '#x' ] && [ "${line}x" != "x" ]; then
        IGNORE_LIST[${idx}]="${line}"
        idx=$((idx + 1))
      fi
    done <"${IGNORE_FILE}"
  fi
  echo "[忽略] ${IGNORE_LIST[*]}"

  install_one_tool "${APP_HOME}"
  install_python_tools

  for rc_file in ${SHELL_RC_FILE[*]}; do
    if [ -f "${rc_file}" ]; then
      echo "[创建链接] ${rc_file}"
      echo ". ${INSTALL_FILE} #MY-TOOLS-PATH DO NOT REMOVE THIS COMMENT" >>${rc_file}
    fi
  done

  notice_msg "安装完成!"
}

install_one_tool() {
  local ignore_flag="0"
  local idx_file
  local command_alias

  # 2. 安装
  for item in "${1}"/*; do
    idx_file="${item#*${APP_HOME}/}"
    ignore_flag="0"

    # 2.1 判断是否被忽略
    for ignore_item in "${IGNORE_LIST[@]}"; do
      if [ "${ignore_item}" == "${idx_file}" ]; then
        ignore_flag="1"
        break
      fi
    done

    # 2.2 安装
    if [ ${ignore_flag} == "0" ]; then
      if [ -d "${item}" ]; then
        # 递归安装
        install_one_tool "${item}"
      elif [ -f "${item}" ]; then
        # 获取命令别名
        command_alias=$(grep -E '^#\s*alias\s*:\s*\S+' "${item}" | awk -F ': ?' '{print $2}' | head -n 1)

        if [ "${command_alias}x" != "x" ]; then
          add_x "${item}"
          printf "alias %s=%s\n" "${command_alias}" "${item}" >>"${INSTALL_FILE}"
          echo "[安装] ${item}"
        fi
      fi
    fi
  done
}

# 卸载函数
uninstall_my_tools() {

  notice_msg "准备卸载 ${APP_HOME}"

  for rc_file in ${SHELL_RC_FILE[*]}; do
    if [ -f "${rc_file}" ]; then
      echo "[解除链接] ${rc_file}"
      sed -i.bak "/#MY-TOOLS-PATH DO NOT REMOVE THIS COMMENT/d" "${rc_file}"
    fi
  done

  if [ -f "${INSTALL_FILE}" ]; then
    echo "[删除] ${INSTALL_FILE}"
    rm -f "${INSTALL_FILE}"
  fi

  uninstall_python_tools

  notice_msg "卸载完成!"
}

# 列出所有命令
list_all_tools() {
  if [ -f "${INSTALL_FILE}" ]; then
    sed -e "/^#/d" -e "/^$/d" "${INSTALL_FILE}"
  else
    echo "尚未安装任何命令"
    helpu
  fi
}

# 版本号函数
my_tools_version() {
  echo && echo "v6.0.0"
}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  helpu
elif [ "$1" = "--install" ] || [ "$1" = "-i" ]; then
  uninstall_my_tools
  install_my_tools
  after_complete
elif [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
  uninstall_my_tools
  after_complete
elif [ "$1" = "--update" ]; then
  update_my_tools
elif [ "$1" = "--list" ] || [ "$1" = "-l" ]; then
  list_all_tools
elif [ "$1" = "--version" ] || [ "$1" = "-v" ]; then
  my_tools_version
else
  helpu
fi
