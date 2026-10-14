# cloak-turnstile

把 [CloakBrowser](https://github.com/CloakHQ/CloakBrowser) 的浏览器启动/指纹配置与 [turnstile-bypass](https://github.com/Sophomoresty/turnstile-bypass) 的 CDP 求解器整合为一个可安装、可测试、可发布的 Python 项目。不是两个仓库的目录拼接，也不依赖子模块。

> 用户原始列表中的 CloakBrowser 重复出现；本项目实际整合两个独立上游。

## 组成

- **一个启动入口**：`cloak-turnstile solve`。
- **一个浏览器实例**：由 CloakBrowser 官方 `launch_persistent_context()` 管理，求解器通过回环地址的 CDP 连接同一实例。
- **复用上游**：保留 turnstile-bypass 的求解器和扩展；不重写挑战逻辑。
- **明确失败**：启动、导航或求解失败返回非零退出码与 `ok: false`；没有普通 Chrome 或其他服务的自动兜底。
- **可发布**：`pyproject.toml`、wheel/sdist 构建、测试、GitHub Actions、上游锁定记录、许可证齐全。

## 环境

- Python 3.10+
- Node.js **22+**，供上游 CDP WebSocket 传输使用
- Windows / macOS 桌面；Linux 需要 DISPLAY/Wayland 或 Xvfb
- 下载 CloakBrowser 浏览器所需的网络和磁盘空间

浏览器保持**有头模式**。没有另行安装 DrissionPage 或普通 Chrome 的要求。

## 安装

从本仓库根目录安装：

```bash
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

`doctor` 只检查依赖、Node 版本、扩展和显示环境，**不代表浏览器已下载或挑战已通过**。`fetch` 使用官方 `ensure_binary()` 下载并验证浏览器。也可直接运行 `solve`，首次启动时自动下载。

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

代理由 CloakBrowser 原生处理，支持其官方 API 接受的协议/认证形式；无需代理认证扩展。可使用环境变量 `CLOAK_TURNSTILE_PROXY`，避免将代理口令写入命令行历史。

强制重新验证：

```bash
cloak-turnstile solve --url https://TARGET/ --profile ./profiles/default --fresh
```

扩展默认加载；`--no-patch` 可显式关闭上游 MouseEvent 扩展，用于对比它与当前 CloakBrowser 二进制的兼容性。扩展保持上游实现，未宣称与所有二进制版本兼容。

Linux 无桌面：

```bash
xvfb-run -a cloak-turnstile solve --url https://TARGET/
```

官方测试站点：

```bash
cloak-turnstile solve --url https://demo.turnstile.workers.dev/ --timeout 45
```

## 输出与退出码

命令结果在 stdout 中是单个 JSON 对象，依赖日志写入 stderr。`--help` 和 `--version` 使用通常的文本输出。

成功必须有长度大于 20 的 token 或 `cf_clearance`，`kind` 为 `turnstile_token` / `cf_clearance` / `both`。仅进入普通页面或上游返回 `cf_passed`，本项目不视为求解成功。

- `0`：结果通过校验。
- `1`：运行错误或没有有效结果。
- `2`：命令行参数解析错误。

Token 有时效性，并可能绑定来源、会话和客户端。测试站点的 dummy token 不代表生产站点可用；没有“任意站点必过”的保证。超时指页面导航和上游求解各自的预算，不包含首次下载，不是整个进程的硬性总时限。

## CloakBrowser 版本与许可

Python 依赖固定为 `cloakbrowser==0.6.2`。`upstream-lock.json` 记录审核时的源码提交，**源码提交记录不等于 PyPI 构建的逐字节身份承诺**。浏览器版本另由官方包选择；需要固定时使用其 `CLOAKBROWSER_VERSION` 环境变量。

本项目只分发 Python 源码和 MIT 上游代码，**不打包浏览器二进制**。CloakBrowser 包装器为 MIT；浏览器二进制适用[独立许可](https://github.com/CloakHQ/CloakBrowser/blob/04c3c027c2b68e0a929a5da1ae5ebf82e3aee423/BINARY-LICENSE.md)。最新版的密钥、并发与订阅限制遵循官方实现；没有修改其授权检查。

可设置 `CLOAKBROWSER_LICENSE_KEY` 使用已有密钥。`CLOAKBROWSER_CACHE_DIR` 可指定下载缓存目录，`CLOAKBROWSER_BINARY_PATH` 可指定已有官方浏览器路径。不要将密钥、profile、浏览器或真实 token 上传 GitHub。

## 开发与验证

```bash
python -m pip install -e '.[dev]'
python -m ruff check src tests
python -m pytest -q
python -m build
```

CI 验证 Python 3.10/3.12/3.13 和 Ubuntu/Windows 上的代码、安装与打包。CI 默认不访问挑战站点；自动化测试验证接口、资源和失败判定，不等同于真实站点通过率测试。

完整设计、来源及验证记录见 [docs/INTEGRATION.md](docs/INTEGRATION.md) 和 [docs/VERIFICATION.md](docs/VERIFICATION.md)。

## 上传 GitHub

在仓库根目录执行（先在 GitHub 创建空仓库，替换 OWNER）：

```bash
git add .
git commit -m "Initial CloakBrowser and Turnstile integration"
git branch -M main
git remote add origin https://github.com/OWNER/cloak-turnstile.git
git push -u origin main
```

已有初始提交时跳过 `git commit`。本地初始化不自动上传，也不自动选用当前机器的 GitHub 账号。

## License

本项目集成代码采用 MIT。复用代码的版权和许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 `licenses/`。
