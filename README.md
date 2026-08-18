# PRAgent — AI Code Review Agent

自动审查 PR Diff，输出结构化问题、修复建议和测试建议。

**核心特性：** GitHub Webhook 集成 · OpenAI 兼容模型 · 多 Agent 并行协作 · 自动修复 · Skill 自进化 · 提示词评测与回滚 · Web 管理台 · Prometheus 指标

## 快速开始

**环境要求：** Python 3.11+

```powershell
python -m pip install -r requirements.txt

$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$env:PRAGENT_AUTH_REQUIRED = 'true'
$env:PRAGENT_AUTH_SECRET = [Convert]::ToBase64String($bytes)
$env:PRAGENT_BOOTSTRAP_ADMIN_USERNAME = 'admin'
$env:PRAGENT_BOOTSTRAP_ADMIN_PASSWORD = '<替换为至少 10 个字符的密码>'

python -m pragent
```

服务默认监听 `http://127.0.0.1:8080`，打开浏览器即可使用 Web 管理台。

## 模型配置

默认使用本地规则 Agent（无需大模型）。通过环境变量切换：

| Provider | 环境变量 |
|---|---|
| DeepSeek 官方 | `PRAGENT_LLM_PROVIDER=deepseek` + `PRAGENT_DEEPSEEK_API_KEY` |
| OpenRouter 免费 | `PRAGENT_LLM_PROVIDER=openrouter-deepseek-free` + `PRAGENT_OPENROUTER_API_KEY` |
| 自定义端点 | `PRAGENT_LLM_PROVIDER=custom` + `PRAGENT_LLM_BASE_URL` / `PRAGENT_LLM_API_KEY` / `PRAGENT_LLM_MODEL` |

密钥只通过环境变量读取。推荐写入根目录 `.env`（已被 `.gitignore` 忽略）。

## API 调用示例

```powershell
# 登录
$session = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/v1/auth/login `
  -ContentType 'application/json' `
  -Body (@{username='admin'; password='<你的密码>'} | ConvertTo-Json)
$headers = @{Authorization="Bearer $($session.access_token)"}

# 提交审查
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/v1/reviews `
  -Headers $headers -ContentType 'application/json' `
  -Body (@{
    repository = 'demo/api'; pull_request = 12
    diff = "diff --git a/app.py b/app.py`n--- a/app.py`n+++ b/app.py`n@@ -1 +1,2 @@`n+password = 'secret'`n+eval(user_input)"
  } | ConvertTo-Json)

# 查询任务
Invoke-RestMethod -Headers $headers http://127.0.0.1:8080/v1/tasks/<task-id>
```

## GitHub Webhook

通过"仓库 Webhook + 公网转发 + fine-grained PAT"接收 PR 事件：

1. **配置环境变量：**
   ```powershell
   $env:PRAGENT_GITHUB_WEBHOOK_SECRET = '<生成的 Webhook Secret>'
   $env:PRAGENT_GITHUB_TOKEN = '<GitHub fine-grained PAT>'  # 可选
   $env:PRAGENT_AUTO_POST_REVIEW = 'true'                   # 可选
   ```

2. **建立公网转发：**
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8080
   # 或 ngrok http 8080
   ```

3. **GitHub 仓库 Settings → Webhooks → Add webhook：**
   - Payload URL: `https://<公网域名>/webhooks/github`
   - Content type: `application/json`
   - Secret: 与环境变量一致
   - 事件: 只勾选 **Pull requests**

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/health` | 健康检查 |
| `POST` | `/v1/auth/login` | 登录获取 Token |
| `POST` | `/v1/reviews` | 创建审查任务（支持 `?async=true`） |
| `GET` | `/v1/tasks/{id}` | 获取任务状态与报告 |
| `POST` | `/v1/tasks/{id}/fix` | 创建自动修复 |
| `POST` | `/v1/tasks/{id}/feedback` | 回流误报/漏报 |
| `POST` | `/webhooks/github` | GitHub PR Webhook |
| `POST` | `/v1/evolution/auto` | 提示词自动进化 |
| `POST` | `/v1/skill-evolution/auto` | Skill 自动进化 |
| `GET` | `/metrics` | Prometheus 指标 |

完整 API 列表见 `.env.example`。

## 生产部署

```powershell
Copy-Item .env.example .env   # 编辑配置
docker compose up --build      # 启动 PostgreSQL + Redis + PRAgent
```

未配置 PostgreSQL/Redis 时自动退回 SQLite + 进程内队列，适合本地演示。

## 架构概览

```text
HTTP / GitHub Webhook
        │
        ▼
 ReviewService ── TaskStore (SQLite / PostgreSQL)
        │
        ▼
 ReviewHarness (Runtime / checkpoint / resume / budget)
        │
        ├── DiffParser
        ├── ContextManager (统一 Token 预算 / 逐轮压缩)
        ├── MemoryManager (working / episodic / semantic)
        └── MultiAgentCoordinator
              ├── Planner → 任务分解
              ├── Specialists (并行): Security · Reliability · LLM · Skills
              ├── Critic → Reflection
              ├── Verifier → 门禁校验
              └── Arbiter → 合并裁决

协作流程：规划 → 初审 → 质疑 → 反思 → 验证 → 裁决
```

## 测试

```powershell
python -m unittest discover -s tests -v
```
