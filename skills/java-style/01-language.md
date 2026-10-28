# 01 语言语法分层

按 JDK 版本给条款，只用到项目实际版本为止。版本来源：`pom.xml` 的 `maven.compiler.release`（无则 `source`），Gradle 的 `java.toolchain.languageVersion` 或 `sourceCompatibility`。

## 0. 闸门

- 不擅自提升 `release`；确实需要更高版本特性时，说明收益与影响面，等确认。
- preview 特性（`--enable-preview`）一律不用。
- 编译参数 `-parameters`（Jackson 反序列化 record 需要）没开时，不假设 record 能被反序列化。

## 1. JDK 8 基线

1. lambda + 方法引用优先于匿名类；`@FunctionalInterface` 标注自定义函数式接口。
2. 接口用 `default` 方法提供可复用默认实现，用 `static` 方法放工厂或工具；不把状态放接口。
3. 空值判断用 `Objects.equals`、`Objects.hash`、`Objects.requireNonNull`，不手写三元判断。
4. 比较器用 `Comparator.comparing(...).thenComparing(...)`；可为空字段用 `Comparator.nullsLast`。

## 2. JDK 9–11

1. 常量集合用 `List.of` / `Set.of` / `Map.of`；超过 10 个键值对用 `Map.ofEntries`；需要可变时 `new ArrayList<>(List.of(...))`。
2. 不需要可变副本时用 `List.copyOf` / `Map.copyOf` 做防御性拷贝。
3. `Optional.isEmpty`、`Optional.ifPresentOrElse`、`Predicate.not`、`Stream.ofNullable` 优先于等价手写。
4. 字符串用 `strip` / `stripLeading` / `stripTrailing`（Unicode 感知）而不是 `trim`；判空用 `isBlank`；重复用 `repeat`；按行处理用 `lines`。
5. `var` 仅用于局部变量，且右侧类型自明（构造器调用、静态工厂、字面量、明确的泛型方法）。禁用场景：字段、方法参数、返回值、右侧是三元表达式、右侧泛型依赖上下文推断、变量名不足以表达类型。
6. `try-with-resources` 可以引用已声明的 effectively final 变量，避免重复声明。

## 3. JDK 12–16

1. 多行 SQL / JSON / HTML 用文本块：`"""` 换行开始，内容左对齐，结尾 `"""` 独占一行。注意文本块会保留行尾空格，拼接动态条件时仍用 `StringBuilder` 或参数化。
2. 字符串格式化用 `formatted` 或 `String.format`；模板化转换用 `transform`（12+）。
3. `Stream.toList()`（16+）返回不可变列表，优先于 `collect(Collectors.toList())`；需要指定容器或可变列表时仍用 `collect`。
4. `instanceof` 模式匹配合并判断与强转：`if (node instanceof OrderNode order) { order.id(); }`，`&&` 右侧可直接使用绑定变量。
5. `record` 的适用面见 [03-modeling.md](03-modeling.md)。

## 4. JDK 17

1. switch 表达式用 `case X ->` 形式，需要分支内多语句时用块加 `yield`。
2. 枚举分支一律用 switch 表达式，且**不写 `default`**，让编译器在新增枚举值时报错；枚举来自外部 jar、无法穷尽时才加 `default`。
3. `sealed interface` / `sealed class` 表达闭合领域（结果类型、状态机、AST）；子类型必须显式声明 `final` / `sealed` / `non-sealed`。
4. 需要可替换随机算法时用 `RandomGenerator` / `RandomGeneratorFactory`；普通场景 `ThreadLocalRandom` 即可（见 07）。

## 5. JDK 21

1. switch 模式匹配：`case null ->`、`case Point(int x, int y) ->` 解构 record、`when` 守卫。只在类型层级闭合（sealed 或枚举）且分支确实按类型分派时使用；能用多态方法覆盖解决的，优先多态。
2. 虚拟线程：仅 IO 密集场景，且项目已是 21、框架版本支持。不要在虚拟线程里再套线程池；避免长时间 `synchronized` 块（会 pin 住载体线程），改用 `ReentrantLock`。
3. `SequencedCollection`：`getFirst` / `getLast` / `reversed`，替代 `list.get(list.size() - 1)` 这类写法。
4. `ExecutorService` 在 21 实现 `AutoCloseable`，局部线程池可用 try-with-resources（关闭时等待任务结束）。

## 6. 常见误用

| 误用 | 后果 | 改法 |
| --- | --- | --- |
| `var grouped = service.query();` | 读代码看不出类型 | 写显式泛型类型 |
| switch 表达式加 `default -> throw ...` | 新增枚举值静默走 default | 删 default，让编译期报错 |
| 用 `Optional` 当字段或参数 | 序列化、相等性、调用方负担 | 字段可空就允许 null 并注释，或返回空对象 |
| 文本块里拼 `+ dynamic +` | 失去可读性且易注入 | 用参数化 SQL 或 `StringBuilder` |
| 为了用新语法把 3 层嵌套 Stream 保留 | 可读性差、调试困难 | 拆方法或改循环 |
