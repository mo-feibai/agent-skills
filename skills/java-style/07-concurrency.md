# 07 并发与异步

## 1. 先判断要不要并发

**适用**：多路相互独立的 IO（RPC、HTTP、DB 批量查询）、批处理分片、非关键路径异步（通知、埋点、日志）。

**不适用**：

- 简单逻辑或单次调用。
- 事务边界内（异步线程不共享事务）。
- 共享可变状态、需要严格顺序。
- CPU 已饱和（加并发只会增加上下文切换）。
- 能用批量接口、`IN` 查询、`UNION` 一次拿完的场景。

先问一句：能不能用一次批量调用替代并发？能就不并发。

## 2. 线程池

1. 优先复用项目已有的 `ThreadPoolTaskExecutor` / `@Async` bean，不重复建池。
2. 必须新建时，四条硬要求：
   - 自定义 `ThreadFactory`，线程名带业务前缀与序号（便于排查）。
   - 有界队列（`ArrayBlockingQueue` 或指定容量），禁用无界 `LinkedBlockingQueue`。
   - 明确拒绝策略：`CallerRunsPolicy`（降级为调用方执行）或抛异常（快速失败），并说明选择理由。
   - 核心数、最大数、队列容量、keepAlive 可配置，不写死在代码里。
3. 禁止 `Executors.newFixedThreadPool` / `newCachedThreadPool` / `newSingleThreadExecutor`（隐藏无界队列或无限建线程）。
4. 生命周期：Spring 管理的池交给容器关闭；方法内局部 `ExecutorService` 用 try-with-resources（JDK 21）或 `finally { shutdown(); }`。
5. 池满与队列堆积要可观测：暴露 `activeCount` / `queueSize` 指标或日志告警。

## 3. CompletableFuture

1. `supplyAsync` / `runAsync` 必须显式传线程池；默认 `ForkJoinPool.commonPool()` 只用于纯 CPU 短任务。
2. 组合方式：
   - 串行依赖 → `thenCompose`。
   - 并行聚合 → `thenCombine` / `allOf` + `join`。
   - 只要先到 → `applyToEither`。
3. 超时必须有：`orTimeout(3, TimeUnit.SECONDS)` 或 `get(timeout, unit)`；没有超时的等待视为缺陷。
4. 异常必须处理：`exceptionally` / `handle` / `whenComplete`；`join()` 抛 `CompletionException`，要取 `getCause()` 转业务异常。
5. 禁止在 `ForkJoinPool` 线程里做阻塞 IO；阻塞任务必须放独立线程池。
6. 不要用 `CompletableFuture` 链做复杂业务编排（多分支、补偿），改用显式状态机或编排器类。

## 4. 异步与事务 / 上下文

1. 事务提交后再发消息：`@TransactionalEventListener(phase = AFTER_COMMIT)` 或 `TransactionSynchronization#afterCommit`；禁止在事务内直接发 MQ。
2. `@Async` 同类自调用不生效（走不到代理）；`void` 返回的 `@Async` 方法异常会被吞，改为返回 `CompletableFuture` 或内部捕获记录。
3. 异步线程拿不到 `ThreadLocal`、`RequestContextHolder`、MDC traceId：用 `TaskDecorator` 显式透传，或把需要的值作为参数传入。
4. 异步方法内的异常必须记录日志，不允许静默失败。

## 5. 共享状态与锁

1. 优先无共享：局部变量、不可变对象、消息传递。
2. 必须共享时用 `ConcurrentHashMap`、`AtomicInteger` / `LongAdder`（高并发计数）、`CopyOnWriteArrayList`（读多写极少）。
3. 复合操作（先查后改）才加锁；单次 CAS 能解决的不用锁。
4. 锁纪律：固定加锁顺序防死锁；锁内不做 IO、不发远程调用；`tryLock` 必须带超时。
5. 分布式锁：必须有过期时间、唯一 value（防误删他人锁）、`finally` 释放；业务执行时间可能超过锁过期时，用续期或改为状态机。
6. `ThreadLocal` 用完必须 `remove()`（线程池复用会残留脏值）；优先用框架提供的上下文传递。

## 6. 幂等

1. 数据库唯一索引兜底，不依赖「先查再插」。
2. 乐观锁：`update ... set version = version + 1 where id = ? and version = ?`，影响行数为 0 即冲突。
3. 重复提交：token 机制、幂等表（业务唯一键唯一索引）、状态机前置校验（只允许 `CREATED → PAID`）。
4. 消息消费幂等：业务唯一键 + 去重表 / Redis `setIfAbsent`，消费失败重试不产生副作用。
5. 幂等键必须落库或落持久化缓存，不能只放 JVM 内存（重启失效、多实例失效）。

## 7. 虚拟线程（JDK 21）

1. 只用于 IO 密集（HTTP、JDBC、文件），且框架/驱动版本已适配。
2. 虚拟线程里不再套线程池；用 `Executors.newVirtualThreadPerTaskExecutor()`。
3. 避免在 `synchronized` 块里阻塞（会 pin 载体线程），改用 `ReentrantLock`。
4. 不要对虚拟线程做池化（创建成本极低，池化反而有害）。
