---
name: java-style
description: 'Java 编码风格与现代语法规范（JDK 8/11/17/21 分层）：Stream、Optional、record、sealed、模式匹配、java.time 与不可变建模，以及解耦模块化、设计模式取舍、并发与线程池、事务与持久化、异常/日志/安全/测试的落地条款。Use when writing, refactoring, or reviewing Java code, choosing a Java syntax feature or API, deciding whether to introduce a design pattern, abstraction or concurrency, or when the user asks Java 编码规范 / 现代 Java 用法 / Stream 怎么用 / Optional 怎么用 / record 能不能用 / Java 代码评审.'
---

# Java 编码风格

适用：JDK 8+ 的 Java 后端项目（Spring Boot / MyBatis 常见）。条款按 JDK 版本分层，只用到项目实际版本为止。
本规范约束人写与 AI 生成、修改的代码。注释与 Javadoc 另见 skill `java-comments`。

## 0. 总则

1. **JDK 闸门**：动手前先读 `pom.xml` 的 `maven.compiler.release` / `source`（或 Gradle 的 `languageVersion`），条款只用得到该版本为止；要升版本先问，不擅自改构建配置。preview 特性一律不用。
2. **新代码达标，存量不回改**：新增文件与本次改动的代码按本规范写；顺带重写相邻旧代码需先说明并获得同意。
3. **语法服务于可读性**：任何新特性用上去如果让代码更难懂，就不算改进；同一文件内跟随既有风格。
4. **项目规范优先**：项目自有规范与本规范冲突时以项目为准，并说明冲突点。
5. **不确定就列方案**：拿不准要不要抽象、要不要并发、record 能否替换时，列 2–3 个方案（含「不做」）与推荐，等用户确认，不自行引入复杂结构。

## 1. 非协商项（每次写 Java 都执行）

1. 只用项目 JDK 支持的语法；不擅自提升 `release`。
2. 集合转换、过滤、分组、聚合优先 Stream；热路径、有副作用、嵌套超 3 层用循环。
3. 可缺失的返回值用 `Optional`，且只用于返回值。
4. 纯数据、不可变、无框架反射要求的载体用 `record`；JPA 实体与需要无参构造 + setter 的类保持 class。
5. 新代码时间统一 `java.time`；禁新增 `java.util.Date` / `Calendar` / `SimpleDateFormat`。
6. 依赖单向、构造器注入 + final 字段、外部系统走接口、Entity 不出 Service 层。
7. 设计模式只在触发条件成立时引入，不为「未来可能」预留抽象。
8. 并发只用于独立 IO、分片、非关键路径异步；线程池必须自定义命名、有界队列、超时与异常处理。
9. 事务边界只放在 Service 公共方法；事务内不做远程调用与大批量 IO。
10. 异常、日志、SQL、缓存、安全按 `09`、`08` 的条款落地；不吞异常、不拼 SQL、不打敏感信息。

## 2. 子文档路由

| 要做的事 | 读 |
| --- | --- |
| 选语法特性：`var`、switch 表达式、模式匹配、文本块、sealed、虚拟线程 | [01-language.md](01-language.md) |
| 集合创建、Stream / Collector、`Map` 惯用法、`Optional`、排序比较 | [02-collections-optional.md](02-collections-optional.md) |
| 设计 DTO/VO/查询结果/枚举、判断能否用 record、Lombok 与 MapStruct 怎么写 | [03-modeling.md](03-modeling.md) |
| 时间、金额、字符串、文件 IO、正则、数值溢出 | [04-time-io.md](04-time-io.md) |
| 分层与依赖方向、包结构、DTO 与 Entity、组合还是继承、何时拆类 | [05-architecture.md](05-architecture.md) |
| 判断该不该上设计模式、用哪个、Spring 里怎么落地 | [06-patterns.md](06-patterns.md) |
| 线程池、`CompletableFuture`、虚拟线程、锁、幂等 | [07-concurrency.md](07-concurrency.md) |
| 事务边界、MyBatis、批量、N+1、缓存三防、数据一致性 | [08-persistence.md](08-persistence.md) |
| 异常与错误码、参数校验、日志、安全、单测 | [09-service-quality.md](09-service-quality.md) |
| 想看正反例 | [examples.md](examples.md) |

## 3. 交付前自检

- [ ] 用到的 API 没有超出项目 JDK 版本，未改 `release`。
- [ ] 没有新增 `Date` / `Calendar` / `SimpleDateFormat`；金额没有 `double`。
- [ ] 没有裸 `Optional.get()`，Optional 没有出现在字段、参数、集合元素里。
- [ ] Stream 没有副作用操作，没有 `parallelStream`，嵌套不超过 3 层。
- [ ] 新增线程池有命名、有界队列、拒绝策略；异步有超时与异常处理。
- [ ] 事务标注在 Service 公共方法，事务内没有远程调用。
- [ ] SQL 全用 `#{}`，没有 `SELECT *`，循环内没有查库。
- [ ] 异常未被吞掉，日志用占位符且无敏感字段。
- [ ] 新增业务逻辑有对应单测，覆盖边界与异常分支。
