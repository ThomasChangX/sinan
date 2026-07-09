# PR Review 协议

> 本文档在**处理 PR review 评论（Copilot / CodeQL）或 CI 失败**时必读。

收到 PR review 评论或 CI 失败时，**严格按以下顺序处理**：

## 1. 推送前本地验证

运行 AGENTS.md 的验证集，全绿后再推送。不要把"本地能跑"等同于"CI 能过"。

```bash
# Python 改动
uv run ruff check src/ && uv run mypy src/sinan && uv run pytest tests/ -v -m "not network"
```

CI 是权威关卡（ADR-0020）。`--no-verify` 绕过本地 hook，**绕不过 CI**。

## 2. 先收集全部问题，再动手修

一次性拉取**所有** CodeQL 评论、**所有** Copilot review 评论、**所有** CI 失败标注，生成完整清单后再写代码。

**禁止**"修一个 → 推一次 → 再看下一个"的循环——这会浪费 CI 配额并让 reviewer 难以追踪。

```bash
# 拉取 PR 上所有 review 评论
gh api repos/{owner}/{repo}/pulls/{pr}/comments
# 拉取 CI 失败日志
gh run view <run-id> --log-failed
```

## 3. 修复后回复并 resolve 每个 review 线程

修代码 ≠ 关评论。每个修复推送后必须三步走：

**(a) 回复**：
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="已修复，见 commit abc123"
```

**(b) Resolve 对话**（无 REST 端点，用 GraphQL）。先获取 thread ID：
```bash
gh api graphql -f query='{ repository(owner:"OWNER",name:"REPO") { pullRequest(number:N) { reviewThreads(first:50) { nodes { id isResolved path } } } } }'
```
再 resolve：
```bash
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "PRRT_xxx"}) { thread { isResolved } } }'
```

**(c) 确认零未解决线程**后再报告完成。只回复不 resolve 会让 PR 视觉上保持 blocked，reviewer 无法判断哪些已处理。

## 4. 先修阻断性基础设施，再做功能

如果 pre-push hook / CI 配置本身坏了（阻断所有人的推送，不只是你的），**先修它**，不要 `--no-verify` 绕过。

用 `actionlint .github/workflows/*.yml` 本地校验 workflow 语法（CI "workflow file issue" 0 秒失败通常是 YAML/语法问题）。

绕过会让问题对所有后续 PR 持续生效。
