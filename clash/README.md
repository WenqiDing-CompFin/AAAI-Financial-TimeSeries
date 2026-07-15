# Clash 固定端口 + 全局代理

本目录提供可直接导入的 Clash / Clash Meta（mihomo）配置，默认：

| 项目 | 值 |
|------|-----|
| 模式 | `global`（全局代理） |
| HTTP / mixed | `7890` |
| SOCKS5 | `7891` |
| redir / tproxy | `7892` / `7893` |
| 控制面板 | `9090` |
| DNS | `1053` |

## 快速使用

1. 编辑 [`config.yaml`](./config.yaml)，把 `proxies:` 下的示例节点替换成你的真实节点。
2. 用 Clash / Clash Verge / Clash Meta / mihomo 加载该文件。
3. 确认面板里 **Mode = Global**，端口与上表一致。
4. 系统或浏览器代理指向：
   - HTTP：`127.0.0.1:7890`
   - SOCKS5：`127.0.0.1:7891`

## 切换模式

配置里当前为全局代理：

```yaml
mode: global
```

如需按规则分流，改为：

```yaml
mode: rule
```

仅直连：

```yaml
mode: direct
```

也可在 Dashboard（`http://127.0.0.1:9090/ui`）里一键切换，无需改文件。

## 固定端口说明

为避免每次订阅更新后端口漂移，本配置**写死**本地监听端口。订阅合并时请保留这些字段，或使用客户端的「覆写 / Override」功能强制写入：

```yaml
mixed-port: 7890
port: 7890
socks-port: 7891
mode: global
external-controller: 0.0.0.0:9090
```

[`override.yaml`](./override.yaml) 可直接作为覆写片段使用。

## 环境变量（终端）

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7891
export no_proxy=localhost,127.0.0.1,::1
```

或执行：

```bash
source clash/env.sh
```

## 校验配置

若已安装 `mihomo` / `clash`：

```bash
mihomo -t -f clash/config.yaml
# 或
clash -t -f clash/config.yaml
```
