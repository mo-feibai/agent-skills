# java-style

Java 编码风格与现代语法规范 skill（Agent Skills 格式，可用于 OpenCode / Claude Code / Codex 等支持 `SKILL.md` 的 agent）。

覆盖范围：

- JDK 分层语法（8 / 11 / 17 / 21）：`var`、switch 表达式、`instanceof` 与 record 模式匹配、文本块、sealed、虚拟线程、`SequencedCollection`
- 集合与 Stream（适用边界、Collector、`Map` 惯用法）、`Optional`（只用于返回值）、比较器
- 数据建模：`record`、sealed、枚举、不可变、参数对象、Lombok 与 MapStruct 边界
- `java.time`、`BigDecimal`、字符串、`Path`/`Files`、正则、数值溢出
- 解耦与模块化：分层与依赖方向、包结构、DTO 与 Entity、组合与继承、拆分信号
- 设计模式：触发条件表、Spring 落地、反模式清单、不确定时列方案
- 并发：线程池、`CompletableFuture`、虚拟线程、锁、幂等
- 持久化：事务边界、MyBatis、批量、N+1、缓存三防、数据一致性
- 工程质量：异常与错误码、参数校验、日志、安全、测试
- 正反例（见 [examples.md](examples.md)）与交付前自检清单

面向 Spring Boot / MyBatis 的 Java 后端项目，条款按项目实际 JDK 分层，只用到该版本为止。

## 安装

```bash
npx skills add mo-feibai/java-style
```

手动安装：把本仓库克隆或复制到任一 agent 全局技能目录，例如：

- OpenCode：`~/.config/opencode/skills/java-style/` 或 `~/.agents/skills/java-style/`
- Claude Code：`~/.claude/skills/java-style/`

安装后新开一个会话即可生效。注释与 Javadoc 规范见配套 skill [java-comments](https://github.com/mo-feibai/java-comments)。

## 触发方式

写、改、审查 Java 代码，或选择语法特性 / 判断要不要抽象、要不要并发时自动加载，或直接说：

- "按 java-style 规范改写这个类"
- "这里该用 record 还是普通类"
- "这段 Stream 要不要改回循环"
- "这个功能适不适合上设计模式"

## 文件

| 文件 | 说明 |
| --- | --- |
| `SKILL.md` | 索引：总则、10 条非协商项、子文档路由表、交付前自检 |
| `01-language.md` | 语法分层与常见误用 |
| `02-collections-optional.md` | 集合、Stream、`Map`、`Optional`、比较器 |
| `03-modeling.md` | record、sealed、枚举、不可变、Lombok/MapStruct |
| `04-time-io.md` | 时间、金额、字符串、文件 IO、数值 |
| `05-architecture.md` | 分层、包结构、边界对象、组合与继承、拆分信号 |
| `06-patterns.md` | 设计模式触发条件、Spring 落地、反模式 |
| `07-concurrency.md` | 线程池、异步、锁、幂等、虚拟线程 |
| `08-persistence.md` | 事务、MyBatis、缓存、数据一致性 |
| `09-service-quality.md` | 异常、校验、日志、安全、测试 |
| `examples.md` | 24 组正反例，按子文档编号归属 |
| `LICENSE` | MIT |

## License

MIT
