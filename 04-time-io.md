# 04 时间、金额、字符串与 IO

## 1. java.time 选型

| 场景 | 类型 |
| --- | --- |
| 只有日期（生日、账期） | `LocalDate` |
| 无时区的业务时间（营业时间、预约时间） | `LocalDateTime` |
| 时间戳、跨时区存储与传输 | `Instant` |
| 需要显式时区（跨时区调度） | `ZonedDateTime` |
| 时长（秒/毫秒级间隔） | `Duration` |
| 日期间隔（天/月/年） | `Period` |

1. 新代码禁用 `java.util.Date`、`Calendar`、`SimpleDateFormat`、`Timestamp`；只在对接旧接口/旧字段时做边界转换，并在转换处注释口径。
2. `DateTimeFormatter` 声明为 `static final` 常量（线程安全）；`SimpleDateFormat` 非线程安全，禁止作为字段共享。
3. 格式优先用 ISO 常量（`DateTimeFormatter.ISO_LOCAL_DATE_TIME`）；自定义 pattern 要写清时区与精度。
4. 时间比较用 `isBefore` / `isAfter` / `isEqual`，不要 `compareTo(...) > 0` 混用多种风格。
5. 需要「现在」时用 `Clock` 注入或 `LocalDateTime.now(clock)`，便于测试；业务代码里散落 `now()` 会导致无法回放。
6. 解析失败抛 `DateTimeParseException`，在边界转成业务异常并带上原值与格式。
7. 序列化：`@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")`；跨时区系统统一存 `Instant` 或 UTC。
8. 数据库字段类型与 Java 类型口径必须写进注释（见 `java-comments`）：`timestamp` ↔ `Instant` / `LocalDateTime` 选一种并全局统一。

## 2. BigDecimal

1. 构造用 `new BigDecimal("0.1")` 或 `BigDecimal.valueOf(0.1)`；禁止 `new BigDecimal(double)`（精度陷阱）。
2. 比较用 `compareTo(other) == 0`；`equals` 会比较 scale，`1.0` 与 `1.00` 判不等。
3. 除法必须给 scale 与 `RoundingMode`：`a.divide(b, 2, RoundingMode.HALF_UP)`；不给会抛 `ArithmeticException`。
4. `setScale` 显式指定舍入模式；不要依赖默认的 `UNNECESSARY`。
5. 金额禁用 `double` / `float` 参与计算；单位（元/分）在字段注释与 DTO 中统一，转换处写明乘除方向。
6. 累加用 `add` 链或 `reduce(BigDecimal.ZERO, BigDecimal::add)`；不要先转 double 再转回。

## 3. 字符串

1. 循环内拼接用 `StringBuilder`（预估容量）；一次性拼接直接用 `+` 或 `String.join`。
2. 格式化用 `formatted` 或 `String.format`；对外文案与日志分开（日志用占位符，见 09）。
3. 判空用 `isBlank()`（含空白字符）；去除首尾空白用 `strip()`（Unicode 感知）。
4. 常量与字面量比较放前面：`"Y".equals(flag)`，避免 NPE。
5. 正则预编译为 `static final Pattern`；`split` 注意元字符转义与 limit 参数。
6. 大小写转换指定 `Locale.ROOT`，避免土耳其语 I 问题。
7. 不用 `String` 做敏感信息容器（不可擦除）；密码/密钥用 `char[]` 或框架提供的类型。

## 4. 文件与 IO

1. 路径用 `Path.of(...)`，文件操作优先 `Files.readString` / `writeString` / `lines` / `walk` / `createDirectories`。
2. 所有流、连接、`Channel` 用 try-with-resources；禁止裸 `FileInputStream` 不关闭。
3. 大文件用流式处理（`Files.lines` + try-with-resources），禁止 `readAllBytes` 读业务文件。
4. 编码显式 `StandardCharsets.UTF_8`，不依赖平台默认编码（Windows 上是 GBK）。
5. 临时文件用 `Files.createTempFile`，用完删除；不在源码目录写中间产物。
6. 网络与 HTTP 客户端复用连接池，不在循环里 new 客户端。

## 5. 数值与溢出

1. 可能溢出的加减乘用 `Math.addExact` / `multiplyExact`，发现溢出即抛而不是静默回绕。
2. 除法前判零；整数除法明确是向下取整还是需要四舍五入。
3. `int` 与 `long` 混算先显式提升；`int` 乘法先转 `long` 再乘。
4. 随机：并发场景用 `ThreadLocalRandom.current()`；需要可复现的测试用固定 seed 的 `Random`；安全场景用 `SecureRandom`。
5. 统计计数在高并发下用 `LongAdder` 而非 `AtomicLong`（见 07）。
