# Agent Skills

个人维护的 agent skills 集合，按 skill 分目录，遵循 opencode 的 `SKILL.md` + frontmatter 约定（`name` / `description`）。

## 安装

```bash
git clone https://github.com/mo-feibai/agent-skills.git
```

把需要的 skill 目录放进宿主扫描的 skills 目录（opencode：`~/.agents/skills/` 或 `~/.config/opencode/skills/`）。

Windows 下想保持单一份源码，用目录联接而不是复制：

```bat
mklink /J "%USERPROFILE%\.agents\skills\token-frugal" "D:\path\to\agent-skills\skills\token-frugal"
```

## 包含的 skill

### token-frugal — 降低 AI 会话的 token 消耗

一条公式：`成本 ≈ 进入上下文的体积 × 它后面还剩多少步`。按六类杠杆组织：读写与命令截断、并行步数、结论复用、子代理隔离、主动回收，附阈值线、工具速查、场景配方与反模式清单。

配套度量脚本，直接读 opencode 的会话库（只读，`mode=ro`）：

```bash
# 最近一个会话
python skills/token-frugal/scripts/session-cost.py

# 指定会话
python skills/token-frugal/scripts/session-cost.py ses_xxx

# 会话排行
python skills/token-frugal/scripts/session-cost.py --top 10

# 换模型价目（输入 / 输出 / 缓存命中，每百万 token）
python skills/token-frugal/scripts/session-cost.py ses_xxx --prices 0.15 0.6 0.003
```

输出：步数、prompt 总量、缓存命中率、实付金额、与「完全不缓存」的对比，以及最大的 5 条工具输出及其占比上界。

skill 里的数字来自一次真实会话的测量，不是估计：1,652 步、473M prompt tokens、命中率 96.5%、实付 $4.96（不缓存需 $72）。

## 许可

MIT，见 [LICENSE](LICENSE)。
