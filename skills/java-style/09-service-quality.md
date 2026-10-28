# 09 异常、校验、日志、安全与测试

## 1. 异常

1. 业务异常继承 `RuntimeException`，携带错误码枚举与参数：
   ```java
   public class BizException extends RuntimeException {
       private final ErrorCode code;
       private final transient Object[] args;
   }
   ```
2. `catch` 必须三选一：能处理则处理、带上下文重抛、记录后抛出；禁止空 `catch` 与只 `e.printStackTrace()`。
3. `catch (Exception e)` 只在最外层（统一出口、定时任务、消息消费）使用，并必须记录完整堆栈。
4. 异常不用于流程控制（用 `Optional` / 判空 / 状态机）。
5. 统一出口：`@RestControllerAdvice` 把业务异常映射为响应码；对外不暴露堆栈、SQL、类名。
6. 受检异常在边界转业务异常，保留 `cause`；不要 `new RuntimeException(e.getMessage())` 丢掉堆栈。
7. 自定义异常不要吞掉原始异常（构造时传 `cause`）；不要复用 `RuntimeException` 表达业务语义。
8. 禁止 `System.out` / `System.err` 输出；禁止 `printStackTrace()`。

## 2. 参数校验

1. Controller 入参用 `@Valid` / `@Validated` + Bean Validation；分组校验（Create / Update）区分场景。
2. 业务规则在 Service 二次校验（注解只能覆盖格式，不能覆盖业务约束）。
3. 校验注解与字段注释一致（非空、长度、范围），不能出现注释写「可空」而注解是 `@NotNull`。
4. `Objects.requireNonNull` 只表达编程错误（调用方违约），不替代业务校验。
5. 校验失败信息面向用户可读，不暴露内部字段名与堆栈。

## 3. 日志

1. 用 SLF4J 占位符：`log.info("下单成功 orderId={} userId={}", orderId, userId)`；禁止字符串拼接与 `+`。
2. 异常日志把异常对象作为最后一个参数：`log.error("下单失败 orderId={}", orderId, e)`；只传 `e.getMessage()` 会丢堆栈。
3. 级别约定：
   - `error`：需要人工介入（数据不一致、依赖不可用、资金异常）。
   - `warn`：可自愈或已降级（重试成功、缓存击穿、限流触发）。
   - `info`：关键业务节点（下单、支付回调、状态流转）。
   - `debug`：排查细节，生产默认关闭。
4. 脱敏：手机号、身份证、银行卡、token、密码、地址不打印完整值；不打全量请求/响应报文。
5. 循环内不打大日志；批量操作按批汇总记录条数与耗时。
6. 链路：MDC 放 traceId，异步线程显式透传（见 07）。
7. 日志文案写清楚「什么对象、什么操作、什么结果」，不写「进来了」「执行了」这类无信息量内容。

## 4. 安全

1. SQL 全参数化（见 08）；禁止拼接用户输入。
2. 输出转义防 XSS；富文本走白名单过滤。
3. 文件上传：校验扩展名与 MIME、限制大小、重命名存储、不放可执行目录、不信任原始文件名。
4. 越权：数据权限条件在 Service/DAO 层拼进查询，不依赖前端隐藏；每个按 id 操作的接口都要校验归属。
5. 密码用 BCrypt / Argon2 加盐哈希；禁止 MD5/SHA1 裸哈希与明文存储。
6. 密钥、AK/SK、连接串走配置中心或环境变量，不进代码、不进日志、不进 git。
7. 反序列化不信任外部输入：禁用 fastjson autoType，Jackson 关闭默认类型信息。
8. 敏感接口做限流与幂等；对外错误信息不泄露内部结构。

## 5. 测试

1. 新增业务逻辑必须配单测：JUnit 5 + AssertJ + Mockito。
2. 覆盖四类：正常路径、边界值（0、负数、最大长度）、异常分支、空集合/空值。
3. 命名：`shouldXxx_whenYyy` 或 `方法名_场景_期望`；一个测试只验证一个行为。
4. 外部依赖（DB、MQ、HTTP）mock；不连真库真中间件；集成测试放独立目录与独立 profile。
5. 不为 getter/setter、纯委托、框架代码写测试。
6. 时间相关逻辑注入 `Clock`；随机相关逻辑注入 `Random`（固定 seed）或封装可替换接口。
7. 并发代码至少测一次「正常并发下结果正确」与「超时/拒绝策略生效」。
