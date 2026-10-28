# Agent Skills

个人维护的 agent skills 集合，按 skill 分目录，遵循 opencode 的 `SKILL.md` + frontmatter 约定（`name` / `description`）。

## 安装

```bash
git clone https://github.com/mo-feibai/agent-skills.git
```

把需要的 skill 目录放进宿主扫描的 skills 目录（opencode：`~/.agents/skills/` 或 `~/.config/opencode/skills/`）。

Windows 下想保持单一份源码，用目录联接而不是复制：

```bat
mklink /J "%USERPROFILE%\.agents\skills\java-style" "D:\path\to\agent-skills\skills\java-style"
```

## 包含的 skill

| skill | 用途 |
| --- | --- |
| [token-frugal](skills/token-frugal/SKILL.md) | 降低 AI 会话的 token 消耗与费用 |
| [java-style](skills/java-style/SKILL.md) | Java 编码风格与现代语法规范 |
| [java-comments](skills/java-comments/SKILL.md) | Java 注释与 Javadoc 规范 |

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

### java-style — Java 编码风格与现代语法规范

按 JDK 8 / 11 / 17 / 21 分层：Stream、Optional、record、sealed、模式匹配、`java.time` 与不可变建模，以及解耦模块化、设计模式取舍、并发与线程池、事务与持久化、异常/日志/安全/测试的落地条款。入口 [`SKILL.md`](skills/java-style/SKILL.md)，细则在 `01-language.md` … `09-service-quality.md`。

### java-comments — Java 注释与 Javadoc 规范

类/接口/枚举注释、方法 Javadoc、字段与常量注释、行内注释与复杂逻辑说明，含正反例、评审检查清单、保密红线与详略规范。

## 许可

MIT，见 [LICENSE](LICENSE)。各 skill 目录内另有其原始 LICENSE。
