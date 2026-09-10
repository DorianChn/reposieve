# RepoSieve

> 面向 AI 编程 Agent 的隐私优先代码仓库上下文打包器。

**v0.5.0 · Beta 免费社区版 · MIT 协议**

RepoSieve 会把代码仓库整理成小而有用、可审阅的上下文包：遵循 `.gitignore`，跳过二进制和生成文件，识别常见密钥格式，默认在本地脱敏，并把结果限制在指定 token 预算内。

不需要 API Key。不上传代码。不采集遥测。

## 快速开始

```bash
python -m pip install .
reposieve scan .
reposieve check .
reposieve pack . --budget 12000 --output context.md
```

不安装也可以运行：

```bash
python -m reposieve pack . --budget 8000
```

生成一份起始配置：

```bash
reposieve init .
```

## 免费版

- 本地扫描仓库；
- 遵循 `.gitignore` 并过滤构建产物；
- 检测和遮蔽常见密钥；
- 生成 Markdown / JSON 上下文包；
- 按近似 token 预算选择文件；
- 适合 CI 的 `check` 命令。

免费版永久免费，代码采用 MIT 协议。

## Pro 一次性买断版

规划价格为每人 **39 美元一次性买断**，不做订阅，不要求把源代码上传到服务器。计划提供本地可视化界面、watch 模式、团队规则包、加密本地快照、上下文差异对比、签名二进制和优先支持。

Pro 商店和二进制尚未宣称上线，详见 [`docs/monetization.md`](docs/monetization.md)。

## 配置

在仓库根目录创建 `.reposieve.toml`：

```toml
[reposieve]
budget_tokens = 12000
max_file_bytes = 256000
redact = true
exclude = ["context.md", "docs/generated/"]
include = ["src/**", "README.md"]
```

命令行参数优先于配置文件。默认开启脱敏；只有在确认内容已在本地审阅后，才使用 `--no-redact`。

也可以只打包指定目录：

```bash
reposieve pack . --include "src/**" --include "README.md" --exclude "src/generated/**"
```

## 开发

```bash
python -m unittest discover -s tests -v
python -m reposieve scan . --json
```

欢迎提交 Issue、改进建议和新的脱敏测试样例。安全边界见 [`SECURITY.md`](SECURITY.md)。
