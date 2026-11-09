# 设计模式的落点与骨架

## 先有判据，后有模式

**模式是「已经做对之后的事后命名」，不是设计时的起点。**

按「我要用策略模式」开始写，通常会得到一个只有一个实现类的接口。正确顺序是：先判断变化维度，再选承载它的最小结构；写完之后发现它正好叫某个模式，那才是真的。

1. **两个实现才是真接缝。** 只有一个实现类的接口是假设出来的接缝。
2. **变体用数据表达优先于用类型表达。** 能写成 `new Ops<>(...)` 的，不要写成 `class RentOps extends BaseOps`。
3. **先问「不做会怎样」。** 抽象不解决眼前的具体问题，就不要抽象。

下面每个骨架都是**示意代码**（4–15 行），表达结构与接缝位置，不是完整实现。

## 速查

| # | 模式 | 解决什么 | 何时用 |
|---|---|---|---|
| 1 | 策略即数据 | 多变体共用一套规则 | 3 张以上同构表 / 3 种以上算法 |
| 2 | 模板方法 | 流程固定、步骤可变 | 环节顺序不能乱，但某一两步因变体而异 |
| 3 | 适配器 | 异构来源或异构环境 | 数据源形状不同、执行上下文不同 |
| 4 | 门面 | 对内多组件、对外一个入口 | 调用方不该知道内部有几个组件 |
| 5 | 建造者 | 配置多、多数可选 | 组装完才求值，中途不产生副作用 |
| 6 | 不可变值对象 | 中间结果跨层传递 | 出参是多字段组合 |
| 7 | 空对象 | 消除 null 分支 | 缺省行为有明确语义 |
| 8 | 双分派 | 类型标签与实现分处两个模块 | 枚举在 common、校验在 system，不能反向依赖 |
| 9 | 规格 | 判定条件复用于多处 | 区间、状态组合判定 |
| 10 | 注册表 + 缓存 | 反射元数据复用 | 注解解析成本高、每次都用到 |
| 11 | 组合优于继承 | 整体动作 = 逐成员做同一动作 | 批量 / 汇总场景 |
| 12 | 声明式横切 | 同一约束施加在几十个方法上 | 权限、数据范围、审计日志 |
| 13 | 事务脚本 | 一个业务动作有明确起止 | 编排层需要控制原子性 |

---

## 1. 策略即数据

```java
// 描述符：只装「变体之间不一样的那几件事」
record LineOps<T extends ContractFeeLine>(
        String feeLineType, String label,
        Function<Long, List<T>> selectByContract,
        Function<Long, T> selectById,
        Consumer<List<T>> batchInsert,
        Consumer<T> updateById,
        Consumer<Long> deleteById,
        Function<T, FeeAmounts> amounts,       // 表专属算钱规则
        boolean addressDerived) {}

// 装配点：每张表一个实例
static final LineOps<DmHouseContractRent> RENT = new LineOps<>(
        "RENT_LINE", "房租",
        rentMapper::selectByContractId, rentMapper::selectById,
        rentMapper::batchInsert, rentMapper::updateById, rentMapper::deleteById,
        ContractFeeLineSupport::rentAmounts, true);

// 通用逻辑：一个泛型方法服务全部变体，不认识表名
<T extends ContractFeeLine> int upsert(LineOps<T> ops, Long contractId, List<T> lines) { ... }
```

**误用信号**：描述符字段 > 15 个 → 变体差异太大，该拆成两个引擎。
**反例**：`abstract class BaseFeeOps { protected abstract ... }` + 三个子类——加第四种表要新建类，且父类 `protected` 方法随时被覆盖导致规则分叉。

## 2. 模板方法

```java
<T extends ContractFeeLine> void normalize(LineOps<T> ops, List<T> lines,
                                           DmHouseContract contract, String defaultAddress) {
    for (T line : lines) {
        normalizeTenant(ops, line, contract);       // 固定步骤
        normalizeAddress(ops, line, defaultAddress); // 固定步骤
        normalizePeriod(ops, line, contract);        // 固定步骤
        normalizeTaxRate(ops, line);                 // 固定步骤
        if (ops.beforeAmount() != null) {            // 钩子
            ops.beforeAmount().accept(line);
        }
        normalizeAmounts(ops, line);                 // 钩子：表专属算法
    }
}
```

**误用信号**：钩子 > 5 个 → 骨架已经不固定了，改成管线（每步一个函数，顺序由数据描述）。

## 3. 适配器

```sql
<!-- 数据侧：各段列名逐字相同，差异只在字面量与 from -->
<sql id="rentLineSelect">
  SELECT 'RENT_LINE' AS fee_line_type, r.rent_id AS fee_line_id, 'RENT' AS bill_type,
         r.contract_id, r.period_start, r.monthly_fee, r.tax_rate, r.dept_id
    FROM dm_house_contract_rent r WHERE r.del_flag = '0'
</sql>
<select id="selectContractLines" resultMap="FeeLineRow">
  <include refid="rentLineSelect"/> UNION ALL
  <include refid="parkingLineSelect"/> UNION ALL
  <include refid="propertyLineSelect"/>
</select>
```

```java
// 环境侧：请求线程与定时线程共用一套取值，调用方不必 try/catch
public static final String SCHEDULE_OPERATOR = "schedule";

public static String username() {
    try {
        return SecurityUtils.getUsername();
    } catch (RuntimeException e) {          // 定时线程没有登录上下文
        return SCHEDULE_OPERATOR;
    }
}
```

**误用信号**：适配器里出现业务判断 → 它开始承担规则，该把规则移到内核。

## 4. 门面

```java
public interface IBillGenerateService {
    int generateForContract(Long contractId, LocalDate asOf);
    int terminateFeeLine(String feeLineType, Long feeLineId, LocalDate terminateDate);
    Long createStandaloneBill(StandaloneBillCommand cmd);
    // …… 21 个方法，内部由 投影 / 内核 / 写入 / 审计 / 校验 5 个组件支撑
}
```

**误用信号**：门面只做纯转发（每个方法只有一行 `return component.xxx()`）→ 没有增值，删掉这一层。

## 5. 建造者（链式配置）

```java
ChangeLogDiffer differ = ChangeLogDiffer.between(before, incoming)
        .resolver(KEY_COMPANY, id -> resolveCompanyName((Long) id))
        .resolver(KEY_OWNER,   id -> resolveOwnerName((Long) id));

if (transferred) {
    differ.skipFields("manageUserId");       // 本次由另一条流水承担
}
List<FieldChange> changes = differ.diff();   // 到这一步才真正计算
```

```java
public ChangeLogDiffer resolver(String key, Function<Object, String> fn) {
    this.resolvers.put(key, fn);
    return this;                             // 只收集配置，不产生副作用
}
```

**误用信号**：链式方法中途就写库或改状态 → 它不是建造者，是过程，链式反而掩盖了副作用。

## 6. 不可变值对象

```java
public record TaxSplit(BigDecimal inclusive, BigDecimal exclusive, BigDecimal tax) {
    public TaxSplit {
        Objects.requireNonNull(inclusive);
        if (inclusive.compareTo(exclusive.add(tax)) != 0) {
            throw new IllegalStateException("税额不守恒");
        }
    }
}
```

```java
// 集合出参要拷贝，否则「不可变」是假的
public record Snapshot(List<Row> rows) {
    public Snapshot { rows = List.copyOf(rows); }
}
```

**误用信号**：`record` 持有可变集合而不 `copyOf`；或在 record 里放 setter 语义的工具方法。

## 7. 空对象

```java
/** 定时任务 / 无登录上下文时落库的操作人 */
public static final String SCHEDULE_OPERATOR = "schedule";

static BigDecimal zeroIfNull(BigDecimal v) { return v == null ? BigDecimal.ZERO : v; }
```

**误用信号**：用空对象掩盖「本该报错」的状态——例如配置缺失返回 0 费率，方向就变成 fail-open。空对象只用于**缺省行为有明确业务语义**的地方。

## 8. 双分派

```java
public interface Gate {                       // 只暴露入口，不含查询
    void asset(Long id);
    void contract(Long id);
    void tenant(Long id);
}

public enum OwnerType {                       // 类型标签在 common 模块
    ASSET   { void check(Gate g, Long id) { g.asset(id);    } },
    CONTRACT{ void check(Gate g, Long id) { g.contract(id); } };

    abstract void check(Gate g, Long id);
}

// 切面：拿到注解上的枚举，直接分派，不需要 switch
scope.value().check(gate, ownerId);
```

**为什么用枚举而不是 switch**：新增一种类型时，编译器强制你实现 `check`；`switch` 会漏 `default` 静默放行。
**误用信号**：枚举里开始写查询逻辑 → 类型标签承载了策略，把查询移回 checker。

## 9. 规格

```java
/** 区间重叠；end 为 null 表示长期有效 */
public static boolean overlaps(LocalDate aStart, LocalDate aEnd,
                               LocalDate bStart, LocalDate bEnd) {
    LocalDate aEndEx = aEnd == null ? LocalDate.MAX : aEnd;
    LocalDate bEndEx = bEnd == null ? LocalDate.MAX : bEnd;
    return !aStart.isAfter(bEndEx) && !bStart.isAfter(aEndEx);
}

// 复用：库里已有账单与待生成账期是否重叠
boolean exists = existing.stream().anyMatch(b -> overlaps(b.start(), b.end(), start, end));
```

**误用信号**：规格对象持有可变状态或依赖外部查询 → 它不是规格，是计算器。

## 10. 注册表 + 元数据缓存

```java
private static final Map<Class<?>, Map<String, FieldMeta>> CACHE = new ConcurrentHashMap<>();

static Map<String, FieldMeta> metadata(Class<?> type) {
    return CACHE.computeIfAbsent(type, ChangeLogFields::parse);   // 每个类只解析一次
}
```

```java
// 解析时发现冲突必须抛，不能静默覆盖
FieldMeta duplicated = ordered.put(meta.getColumn(), meta);
if (duplicated != null) {
    throw new IllegalStateException(type.getName() + " 的列名重复：" + meta.getColumn());
}
```

**误用信号**：缓存没有失效策略而数据会变（内存泄漏）；或解析冲突时后者覆盖前者（流水记到错误字段，极难排查）。

## 11. 组合优于继承

```java
public int onContractTerminated(Long contractId, LocalDate terminateDate) {
    int affected = 0;
    for (FeeLineRow line : feeLineMapper.selectContractLines(contractId)) {
        affected += terminateLineInternal(line, terminateDate, "合同退租");  // 复用单条逻辑
    }
    return affected;
}
```

**误用信号**：组合后不返回汇总（总数、失败清单）→ 调用方还得自己再查一遍。

## 12. 声明式横切

```java
@RequireOwnerScope(OwnerType.CONTRACT)          // 注解只声明「是什么」
@PostMapping("/{contractId}/terminate")
public AjaxResult terminate(@PathVariable Long contractId) { ... }
```

```java
@Around("@annotation(scope)")
public Object around(ProceedingJoinPoint pjp, RequireOwnerScope scope) throws Throwable {
    gate.denyAll();                              // 入场先写拒绝哨兵，fail-closed
    checkerFor(scope.value()).check(ownerIdOf(pjp));   // checker 决定「怎么办」
    return pjp.proceed();
}
```

**误用信号**：切面默认放行、或捕获异常后不中断 → 最危险的一类 bug：漏一处 = 权限全开，且日志里看不到。

## 13. 事务脚本

```java
@Transactional(rollbackFor = Exception.class)
public int generateForContract(Long contractId, LocalDate asOf) { ... }          // 跟随调用方事务
```

```java
@Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public int generateForContractInNewTx(Long contractId, LocalDate asOf) {
    return generateForContract(contractId, asOf);   // 批量路径：单份失败不拖累整批
}
```

**误用信号**：事务边界藏在被调服务里 → 调用方无法控制原子性；或用 `boolean batchMode` 运行时切换事务语义。

---

## 模式组合：一个引擎用了哪几个

出账引擎 = **适配器**（SQL 投影）+ **策略即数据**（条款差异）+ **模板方法**（单期生成骨架）+ **不可变值对象**（Period / TerminateEffect）+ **门面**（对外 21 个方法）+ **声明式横切**（权限注解）+ **事务脚本**（编排层）。

这不是刻意套用，是每个维度各自找到了最小的承载结构。

## 不要这样用

| 反模式 | 表现 | 为什么错 |
|---|---|---|
| 一个实现的策略接口 | `interface FooStrategy` + `FooStrategyImpl` | 假设出来的接缝，只增加跳转成本 |
| 工厂造工厂 | `FooFactory.createBarFactory()` | 抽象层级超过实际问题复杂度 |
| 观察者做同步调用 | `notifyAll()` 里直接执行业务 | 事件语义被当成方法调用，失败无法回滚 |
| 单例持有请求状态 | 静态字段存 `userId` | 并发串号，测试无法隔离 |
| 装饰器层层包裹 | 5 层 wrapper 只为加一行日志 | 横切用 AOP，嵌套用组合 |

## 三个问题

1. **变化维度是什么？** 形状 → 适配器；行为 → 策略；时机 → 模板方法 / 事件；环境 → 适配器。
2. **有几个真实变体？** 1 个 → 不抽象；2 个 → 可以抽；3 个以上 → 必须抽，优先用数据表达。
3. **不做会怎样？** 答案是「现在也没问题」→ 不做。

## 与「唯一写入点」的关系

模式解决「怎么组织代码」，唯一写入点解决「谁有权改数据」。两者必须分开：

- 用策略模式让 3 种计费方式共存 → 好。
- 用策略模式让 3 个服务各自 `UPDATE` 账单 → 坏。

**能被模式替代的是分支，不能被替代的是收口。**
