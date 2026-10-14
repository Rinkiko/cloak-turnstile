# Cloak Turnstile

[![CI](https://github.com/Rinkiko/cloak-turnstile/actions/workflows/ci.yml/badge.svg)](https://github.com/Rinkiko/cloak-turnstile/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**面向浏览器自动化的 Turnstile 验证处理工具。**

通过一个命令启动浏览器、访问目标页面、尝试处理验证并输出结构化结果。支持独立会话、持久化配置、代理与地域参数，适合接入脚本和自动化流程。

## 功能

- **验证处理**：尝试处理 Turnstile 组件和 Cloudflare 等待验证页。
- **会话管理**：临时会话自动清理，指定配置目录后保留 Cookie 和 localStorage。
- **环境配置**：支持代理、指纹种子、语言、时区及可选 GeoIP。
- **结构化输出**：stdout 返回单个 JSON 对象，诊断日志写入 stderr。
- **明确的失败状态**：运行错误返回非零退出码，不自动切换浏览器或求解服务。

## 环境

- Python 3.10+
- Node.js **22+**，供上游 CDP WebSocket 传输使用
- Windows / macOS 桌面；Linux 需要 DISPLAY/Wayland 或 Xvfb
- 下载浏览器运行时所需的网络和磁盘空间

浏览器保持**有窗口模式**，Linux 需要桌面环境或 Xvfb。

## 安装

获取项目并创建虚拟环境：

```bash
git clone https://github.com/Rinkiko/cloak-turnstile.git
cd cloak-turnstile
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\cloak-turnstile.exe doctor
.\.venv\Scripts\cloak-turnstile.exe fetch
```

macOS / Linux：

```bash
.venv/bin/python -m pip install -e .
.venv/bin/cloak-turnstile doctor
.venv/bin/cloak-turnstile fetch
```

`doctor` 只检查依赖、Node 版本、扩展和显示环境，**不代表浏览器已下载或挑战已通过**。`fetch` 下载并校验官方浏览器安装文件。也可直接运行 `solve`，首次启动时自动下载。

需要 GeoIP 时：`python -m pip install -e '.[geoip]'`。

## 使用

下面命令假定已激活虚拟环境；也可把 `cloak-turnstile` 替换成 `python -m cloak_turnstile`。将 `https://TARGET/` 替换为目标页面。

```bash
cloak-turnstile solve --url https://TARGET/ --timeout 45
```

保留 Cookie、localStorage 和指纹种子：

```bash
cloak-turnstile solve --url https://TARGET/ --profile ./profiles/default --seed 12345
```

同一 profile 不要同时用于多个进程。临时 profile 会在浏览器关闭后清除；指定的 profile 不会被清除。`cf_clearance` 留在指定 profile 中，JSON 只输出长度和域名。若需要沿用会话，应始终使用同一 profile、IP 和浏览器配置。

代理与地域配置：

```bash
cloak-turnstile solve --url https://TARGET/ --proxy http://HOST:PORT --timezone Asia/Shanghai --locale zh-CN
cloak-turnstile solve --url https://TARGET/ --proxy socks5://HOST:PORT --geoip
```

代理由浏览器运行时处理，支持其官方 API 接受的协议/认证形式。可使用环境变量 `CLOAK_TURNSTILE_PROXY`，避免将代理口令写入命令行历史。

强制重新验证：

```bash
cloak-turnstile solve --url https://TARGET/ --profile ./profiles/default --fresh
```

鼠标事件兼容扩展默认加载；`--no-patch` 可显式关闭，便于比较不同浏览器版本下的效果。兼容性取决于浏览器版本和目标页面。

Linux 无桌面：

```bash
xvfb-run -a cloak-turnstile solve --url https://TARGET/
```

官方测试站点：

```bash
cloak-turnstile solve --url https://demo.turnstile.workers.dev/ --timeout 45
```

## 输出与退出码

| 命令 | 作用 |
|---|---|
| `doctor` | 检查依赖与显示环境 |
| `fetch` | 下载并校验浏览器安装文件 |
| `solve --url URL` | 打开页面并尝试处理验证 |

命令结果在 stdout 中是单个 JSON 对象，依赖日志写入 stderr。`--help` 和 `--version` 使用通常的文本输出。

客户端结果检查要求长度大于 20 的 token 或 `cf_clearance`，`kind` 为 `turnstile_token` / `cf_clearance` / `both`。仅进入普通页面不算验证成功。**长度检查不等于目标网站的服务端接受。**

- `0`：结果通过校验。
- `1`：运行错误或没有有效结果。
- `2`：命令行参数解析错误。

Token 有时效性，并可能绑定来源、会话和客户端。测试站点的 dummy token 不代表生产站点可用；没有“任意站点必过”的保证。超时指页面导航和验证处理各自的预算，不包含首次下载，不是整个进程的硬性总时限。

命令结束后关闭浏览器。项目不包含自动登录、批量采集、代理池或图形管理界面，后续业务操作需要单独接入。

## 运行配置

浏览器运行时依赖固定为 `cloakbrowser==0.6.2`。运行时负责浏览器版本选择、下载校验和许可管理。需要固定浏览器版本时使用 `CLOAKBROWSER_VERSION`。

| 环境变量 | 用途 |
|---|---|
| `CLOAK_TURNSTILE_PROXY` | 默认代理地址 |
| `CLOAKBROWSER_CACHE_DIR` | 浏览器下载缓存目录 |
| `CLOAKBROWSER_BINARY_PATH` | 已有浏览器可执行文件路径 |
| `CLOAKBROWSER_LICENSE_KEY` | 已有运行时密钥 |
| `CLOAKBROWSER_VERSION` | 浏览器版本配置 |

不要将密钥、profile、浏览器或真实 token 上传 GitHub。

## 开发与验证

```bash
python -m pip install -e '.[dev]'
python -m ruff check src tests
python -m pytest -q
python -m build
```

CI 验证 Python 3.10/3.12/3.13 和 Ubuntu/Windows 上的代码、安装与打包。CI 默认不访问挑战站点；自动化测试验证接口、资源和失败判定，不等同于真实站点通过率测试。

更多信息：[运行架构](docs/INTEGRATION.md) · [验证记录](docs/VERIFICATION.md) · [问题反馈](https://github.com/Rinkiko/cloak-turnstile/issues)。

## 许可与第三方组件

本项目代码采用 [MIT](LICENSE)。第三方组件的来源、修改说明及版权见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 `licenses/`。浏览器二进制由运行时从官方渠道获取，不包含在本仓库中，其许可独立于本项目。
