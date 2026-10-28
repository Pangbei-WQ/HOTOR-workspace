# 项目长期记忆

## 本工作空间是什么

`HOTOR-workspace`（火蛋科技）**同时是一个 Obsidian vault**，采用 Karpathy LLM Wiki 架构，框架与 Agent 操作方法移植自参考仓库 `Pangbei-WQ/My-Personal-Obsidian`。

- 定位：业务（HOTOR）+ 个人成长 混合知识库，业务为主
- 双层：`raw/` 原始资料（只读不可变） + `wiki/` LLM 维护层
- 领域：`wiki/HOTOR业务/`、`wiki/个人成长/`、`wiki/AI与工具/`、`wiki/工作方法/`
- 远端：`origin = https://github.com/Pangbei-WQ/HOTOR-workspace.git`（分支 main）

## 关键约束（必须遵守）

- **工作规则见根目录 `AGENTS.md`，需 100% 遵守**。核心红线：
  - `raw/` 只读不可变（唯一例外：按收件箱六步流程"移动"归档，不改内容）
  - `raw/知识文件归档/Daily/` 只读，日记是私人空间
  - `wiki/` 可读写，但每次改动必须同步更新 `wiki/index.md` 与 `wiki/log.md`
  - **`review_status` 绝不可设为 `reviewed`** —— 这是人工专属权限，LLM 只能设 `unreviewed` / `disputed` / `outdated`
  - 已 `reviewed` 的页面不得改原文，只能在下方追加"更新块"
  - `AGENTS.md` 修改前需人工确认
- 不得改动 `.obsidian/`、`.claude/`、`.claudian/`（均为 gitignore）

## 工作方式偏好（用户明确要求，2026-10-27）

- **先计划后动手**：产物类任务先在对话里给方案/大纲，用户确认后再落地生成
- 用户会就方案细节逐项拍板，回答后再执行

## 本机环境坑

- 直连 GitHub 的 git/curl 曾出现 schannel TLS 握手失败；可用时优先 `git ls-remote` 探测，再 `curl -o x.zip` 下载 codeload zip 解压（比 `git clone` 稳定）
- 本机无 `gh` CLI；网页抓取通道（WebFetch）可用但结果有缓存
- Read 工具需 Windows 真实路径，Git Bash 的 `/tmp` 对应 `C:/Users/HDKJ/AppData/Local/Temp`
