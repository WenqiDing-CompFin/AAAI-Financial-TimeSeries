#!/usr/bin/env bash
# 将 Clash 固定端口写入当前 shell 环境变量
# 用法: source clash/env.sh

export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7891
export ALL_PROXY=socks5://127.0.0.1:7891
export no_proxy=localhost,127.0.0.1,::1
export NO_PROXY=localhost,127.0.0.1,::1

echo "Clash proxy env set: HTTP/HTTPS -> 127.0.0.1:7890, SOCKS5 -> 127.0.0.1:7891"
