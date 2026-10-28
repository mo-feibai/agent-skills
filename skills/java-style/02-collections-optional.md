# 02 集合、Stream 与 Optional

## 1. 集合创建与返回

1. 常量或只读集合用 `List.of` / `Set.of` / `Map.of` / `Map.ofEntries`；不要 `Arrays.asList` 之后再 `add`（固定长度会抛异常）。
2. 需要可变副本时 `new ArrayList<>(List.of(...))`、`new HashMap<>(Map.of(...))`。
3. 对外返回集合永不返回 `null`，返回空集合；需要防篡改时返回 `List.copyOf` 或 `Collections.unmodifiableList`。
4. 已知规模时给 `ArrayList` / `HashMap` 预估容量（元素数 / 0.75 + 1），避免反复扩容。

## 2. Stream 的适用边界

**用 Stream**：集合转换、过滤、分组、聚合、扁平化、一次性链式表达意图。

**不用 Stream**：

- 热路径（高 QPS、单次微秒级、循环体内百万级迭代）。
- 需要 `break` / `continue` / 多层 `return` 的循环。
- 需要下标、需要同时访问相邻元素。
- 逻辑中要抛受检异常。
- 链式超过 3 层仍说不清意图。

**硬约束**：

1. 中间操作保持无副作用；`peek` 只用于调试，禁止在里面改外部状态。
2. 禁止用 `forEach` 修改外部集合，用 `collect` 收集结果。
3. 禁止 `parallelStream` 处理 IO 或共享可变状态；纯 CPU 且数据量大时才考虑，并说明理由（见 07）。
4. 不吞受检异常：要么在 lambda 内包成 `UncheckedIOException` / 业务异常并保留 cause，要么改回循环。

## 3. 常用操作与 Collector

| 需求 | 写法 |
| --- | --- |
| 找第一个 | `stream().filter(...).findFirst()` |
| 是否存在 / 全满足 | `anyMatch` / `allMatch` / `noneMatch` |
| 去重 | `distinct()`（依赖 `equals`） |
| 排序 | `sorted(Comparator.comparing(...))` |
| 分组 | `collect(groupingBy(Order::status))` |
| 分组计数 | `groupingBy(Order::status, counting())` |
| 分组求和 | `groupingBy(Order::status, summingLong(Order::amount))` |
| 分组后取字段 | `groupingBy(..., mapping(Order::id, toList()))` |
| 分区 | `partitioningBy(Order::isPaid)` |
| 拼字符串 | `collect(joining(",", "[", "]"))` |
| 转 Map | `toMap(Order::id, o -> o, (a, b) -> a)`，必须给合并函数 |
| 同时求两个聚合 | `teeing(counting(), summingLong(...), ...)` |
| 展平 Optional | `flatMap(Optional::stream)` |

1. `toMap` 不给合并函数时重复 key 直接抛异常，线上必现；一律显式给 `(a, b) -> a` 或 `(a, b) -> b`。
2. 数值聚合用 `mapToInt` / `mapToLong` 避免装箱；需要一次求多个统计量用 `summaryStatistics`。
3. 区间遍历用 `IntStream.range` / `rangeClosed`，不要 `for` 里手工拼集合再转流。

## 4. Map 惯用法

1. 计数：`map.merge(key, 1L, Long::sum)`。
2. 分组初始化：`map.computeIfAbsent(key, k -> new ArrayList<>()).add(value)`。
3. 取默认值：`map.getOrDefault(key, defaultValue)`；默认值有构造成本时改用 `computeIfAbsent`。
4. 不存在才放：`putIfAbsent`；判断值相等再删：`remove(key, value)`。
5. 遍历用 `entrySet()`；批量删除用 `entrySet().removeIf(...)`，不要在 `keySet` 遍历中 `remove`。

## 5. Optional

1. **只用于返回值**。禁止：字段、方法参数、集合元素、`Map` 的 value、数组元素。
2. 构造：确定非空用 `Optional.of`，可能为空用 `ofNullable`，空用 `empty`。
3. 链式：`map`（值转换）、`flatMap`（返回 Optional）、`filter`、`or`（Supplier 提供备选 Optional）。
4. 取值：
   - 有常量默认值 → `orElse(value)`。
   - 默认值需要构造或查询 → `orElseGet(() -> ...)`（`orElse` 会先求值）。
   - 缺失即异常 → `orElseThrow(() -> new BizException(ErrorCode.NOT_FOUND))`。
   - 禁止裸 `get()`。
5. 分支：`ifPresent` / `ifPresentOrElse`；不要 `if (opt.isPresent()) { opt.get(); }`。
6. 集合里可能有空值：`stream().flatMap(Optional::stream)`。
7. 不要用 `Optional` 包装集合；空集合本身就是「没有」。
8. 返回 `Optional` 的方法不要同时返回 `null`。

## 6. 比较与排序

1. 多字段排序：`Comparator.comparing(Order::getCreatedAt).thenComparing(Order::getId)`。
2. 反序用 `reversed()`；空值排后 `Comparator.nullsLast(...)`。
3. 基本类型用 `comparingInt` / `comparingLong` / `comparingDouble`，避免装箱。
4. 禁止 `(a, b) -> a - b` 手写比较（溢出）。
5. 比较字符串排序规则要写清 Collator / `Locale.ROOT`，中文排序不依赖默认 Locale。
