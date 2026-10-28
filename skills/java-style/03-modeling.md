# 03 数据建模：record、sealed、枚举、不可变

## 1. record

**用**：DTO / VO / 查询结果 / 领域事件 / 方法多返回值 / 参数对象 / 值对象（金额、区间、坐标）。

**不用**：

- JPA `@Entity`（需要无参构造、代理、可变状态）。
- MyBatis 需要无参构造 + setter 的 DO。
- 需要继承、需要大量可变字段、需要 Jackson 循环引用处理的对象。
- 项目未开 `-parameters` 编译参数时，作为 `@RequestBody` 反序列化目标（Jackson 拿不到构造器参数名）。

**写法**：

1. 校验与规范化放紧凑构造器：`Objects.requireNonNull`、`trim`、范围检查；不要在校验失败时静默修正。
2. 集合字段在构造器里 `List.copyOf(...)` / `Map.copyOf(...)`，避免外部持有可变引用。
3. 派生值用实例方法，不额外声明字段（record 不允许实例字段）。
4. 需要可变演进时用 `with` 式方法返回新实例，不提供 setter。
5. `toString` 有敏感字段时重写并脱敏。

## 2. sealed

1. 适用：闭合结果集（`Success` / `Failure`）、状态机状态、表达式树、有限命令集合。
2. 子类型必须显式 `final` / `sealed` / `non-sealed`；不能遗漏修饰符。
3. 配合 switch 模式匹配使用，穷尽性由编译器保证；不要为了「以后可能加类型」而 sealed，那种场景应该是普通接口。
4. sealed 接口的 permits 子句可省略（同一文件内自动推断），跨文件必须显式列出。

## 3. 枚举

1. 用枚举替代 `int` / `String` 常量；枚举带字段、构造器、实例方法，把相关行为收到枚举里（如 `canTransitionTo`）。
2. 枚举分支用 switch 表达式且不写 `default`（见 01）。
3. 持久化用显式 `code` 字段 + `@EnumValue`（MyBatis-Plus）或自定义 `TypeHandler`；**禁用 `ordinal()`**，顺序一变数据全错。
4. 外部接口传值用 `code` 而非 `name()`；`name()` 只用于日志与配置。
5. 每个枚举值必须有业务含义注释（见 `java-comments`）。

## 4. 不可变与防御

1. 字段能 `final` 就 `final`；集合字段初始化即不可变。
2. 入参集合先 `List.copyOf` 再用；出参集合返回不可变视图或副本。
3. 参数超过 4 个（或含多个同类型参数）→ 参数对象（record）或建造者；禁止 `create(String a, String b, String c, String d, String e)`。
4. 布尔参数禁用：`send(orderId, true)` 无法阅读，改成枚举 `SendMode.IMMEDIATE`。
5. 可变对象不要作为 `HashMap` key 或 `Set` 元素。

## 5. Lombok 与 MapStruct 边界

1. `@Data` **不用于** JPA 实体：生成的 `equals` / `hashCode` 会触发懒加载、破坏代理。实体用 `@Getter` / `@Setter`，需要相等性时显式 `@EqualsAndHashCode(of = "id")`。
2. 构造器注入用 `@RequiredArgsConstructor` + `private final` 字段；不用字段 `@Autowired`。
3. `@Builder` 用于参数多或有可选参数的对象；与 `@NoArgsConstructor` 同用时记得补 `@AllArgsConstructor`，否则编译失败。
4. `@ToString` 排除敏感字段与大集合（`@ToString.Exclude`）。
5. MapStruct 只做 DTO ↔ Entity/DO 的字段映射；字段名不一致显式 `@Mapping(source, target)`；禁止 `unmappedTargetPolicy = IGNORE` 掩盖漏映射。
6. 不用 Lombok 的 `@SneakyThrows` 绕过受检异常；不在 record 上叠加 `@Data`。
