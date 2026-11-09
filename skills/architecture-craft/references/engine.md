# 引擎设计

引擎 = 把会变化的维度收进输入，让调用方的代码保持不变。

## 1. 五段流水线

| 段 | 职责 | 边界条件 |
|---|---|---|
| ① 投影 Adapter | 异构数据源 → 统一行类型 | 只做映射，不做判断 |
| ② 内核 Kernel | 做决定：算期、算钱、算处置 | 无 IO、无 Spring、无事务、无请求上下文 |
| ③ 编排 Orchestrator | 范围、锁、事务、失败隔离 | 认识外部世界，不认识计算规则 |
| ④ 唯一写入点 | 校验 + 快照 + 编号 + 审计 | 所有出账路径最终都汇到这里 |
| ⑤ 执行报告 | 告知调用方发生了什么 | `record`，不是 `int` |

**② 的核心价值不是复用代码，是让规则有物理边界。** 内核不查库，就看不到已有数据，也就没有机会去改它——「已生成的事实不可变」这条业务规则由分层保证，不靠 code review。

## 2. 输入三分法

设计引擎签名时，先把每个入参归到三类之一：

| 形态 | 判据 | 代码形态 | 选错的后果 |
|---|---|---|---|
| **整体数据 eager** | 所有变体都需要，缺一个就算错 | `LineRow line` | 做成可选 → 内核里到处判空 |
| **旁路集合 optional** | 只有部分变体需要 | `List<FreePeriod> periods`（不需要就传空集合） | 做成必填 → 污染全部调用方 |
| **按需回调 lazy** | 只用到一小片，且取数代价高 | `Function<LocalDate, RentBase> resolver` | 做成 eager → 预加载全部历史；做成内部查库 → N+1 |

**回调形态最值得学**：内核只在算递增时问「这一天的基准是多少」，它不知道 `rent_history` 这张表存在。表名、查询条件、缓存策略全留在调用方。将来换存储，内核一行不改。

## 3. 投影层：形状放 SQL，行为放代码

| 差异性质 | 放哪 | 形态 |
|---|---|---|
| 数据形状（不同表、不同来源） | SQL | 每张表一段 `SELECT`，**列名逐字相同**，只差常量字面量和 from 子句，`UNION ALL` 成同一个 resultMap |
| 数据来源在运行时才知道 | Checker / 分派层 | 先查一条，再决定查哪张表 |
| 行为不同（算法不同） | 代码 | 策略 / 描述符 / 回调 |

判据：**这个变体是「数据长得不一样」还是「做事的方式不一样」？** 前者进 SQL，后者进代码。

把形状差异放进 Java 分支，等于让引擎知道「世界上有几种费用」。这句话一旦成立，引擎就不再是引擎。

投影落地时的硬约束：
- 列名必须逐字相同，差异只允许出现在字符串字面量里（`'RENT_LINE'` / `'PARKING_LINE'`）。
- 一个 `<sql>` 片段一段来源，`UNION ALL` 拼装；新增来源只加一段，不改已有段。
- resultMap 只写一次，新增来源复用它。

## 4. 四种抽象形态

按「吸收什么变化」选形态，不要一律上策略模式：

| 形态 | 吸收的变化 | 表达方式 | 典型场景 |
|---|---|---|---|
| 公式引擎 | 数值口径 | 静态方法 + `record` 出参 | 算税、算日租金、算期间重叠 |
| 投影 + 内核 | 数据源结构 | SQL 打平 → 统一行 → 纯函数 | 多表同构出账 |
| 描述符引擎 | 表与表的差异 | `record Ops<T>` 注入若干函数 | 三张条款表共用一套校验 |
| 声明式引擎 | 字段 / 方法级差异 | 注解 + 回调表 | 变更流水、权限闸门 |

描述符优于继承的理由：继承把变体绑成编译期依赖，父类的 `protected` 方法随时可能被覆盖导致规则分叉；描述符是**数据**，加变体只是 `new Ops<>(...)`，通用逻辑完全不知道有新变体存在。

## 5. 引擎接口六条规则

1. **构造即校验**：`static of(...)` 内部跑 `validate()`，之后所有公开方法可假定输入合法。
2. **出参用 record**：调用方不能顺手改中间结果，字段语义写在 `@param`。
3. **扩展点用函数参数**：`Function<LocalDate, RentBase>` 而不是 `boolean enableIncrement`。开关一多就组合爆炸。
4. **失败显式**：未知枚举值直接抛，不兜底成默认值。配置错静默按 0 算，比报错危险得多。
5. **不查库、不改事实**：是否已存在由编排层判断。
6. **入口一个，出口按问题分**：一个 `of()` 产出一个已校验实例；`schedule` / `simulateTerminate` / `amountFor` / `overlaps` 分别回答调用方不同的问句。这不是胖接口，是深接口。

## 6. 环境假设收口

同一段代码既在请求线程跑，也在定时线程跑时，把「当前操作人从哪来」收口成一个类：

```java
public final class OperatorContext {
    public static final String SCHEDULE_OPERATOR = "schedule";
    public static String username() { try { return SecurityUtils.getUsername(); } catch (RuntimeException e) { return SCHEDULE_OPERATOR; } }
    public static Long userId() { try { return SecurityUtils.getUserId(); } catch (RuntimeException e) { return null; } }
}
```

**约束：「当前操作人从哪来」这个假设，在整个引擎里只允许在一个类里成立。**

于是引擎里没有一行 `try { SecurityUtils... } catch`。将来换认证框架、加租户上下文、放 MQ 消费，只改这一个类。

同类：把「管理处必须在部门子树内」「含税价怎么拆」抬成共享件。判据是——**这条规则一旦有第二个人需要，复制就一定会发生**。

## 7. 幂等：键选型 + 两层防线

| 键 | 表达的事实 | 重跑时 |
|---|---|---|
| 自增主键 | 「同一行」 | 产生新行，永远无法判重 |
| `(line_type, line_id, period_start)` | 「同一条款的同一期」 | 撞唯一索引 → 判定已生成 |

键选对之后，判定逻辑可以从「等值」放宽到「区间重叠」——因为免租顺延、终止收口会让起止变化，等值比较会判漏。

两层防线，目的不同：

| 层 | 负责 | 单独用会怎样 |
|---|---|---|
| 应用层（区间重叠判定） | 可读语义、可单测、能说清「为什么跳过」 | 并发下两个线程都通过 → 重复 |
| 数据库层（函数唯一索引，`DECODE` 排除软删行） | 并发、重跑、绕过代码时的最终保证 | 只能报「唯一约束冲突」，说不出业务原因 |

**代价**：两层必须同步演进。改了 `WHERE` 条件却忘了改前面的 `SELECT` 校验，文案就会说谎。

## 8. 并发：条件写进 WHERE，用影响行数判定

```java
if (mapper.updateAmount(billId, amount, user) == 0) {
    throw new ServiceException("正被其他操作登记收款或核销，修改已回滚，请刷新后重试");
}
```

```sql
UPDATE bill SET amount_due = #{amount}
 WHERE bill_id = #{id}
   AND COALESCE(del_flag,'0') = '0'
   AND COALESCE(amount_paid, 0) = 0
   AND COALESCE(writeoff_status,'UNCONFIRMED') <> 'CONFIRMED'
```

前面的 `SELECT` 校验只负责给出精确的中文报错；**真正的保证在 `WHERE` 里**。检查与动作之间永远有窗口，把前提写成条件、把结果写成影响行数，窗口就不存在了。

## 9. 返回值：表达处置，不表达成败

```
TerminateEffect(TerminateAction action, LocalDate newPeriodEnd, BigDecimal newAmount)
  VOID    → 整期在终止日之后      → 作废 + 流水
  SHRINK  → 跨终止日的未付期      → 按天收口
  KEEP    → 已付                  → 不动，只记流水
```

返回 `boolean success`，调用方就得自己判断「作废还是收口、收到哪天、金额多少」——规则从引擎漏回调用方了。

判据：**这个方法的输出里，有没有调用方必须知道、但引擎已经算出来的信息？** 有 → `record`，不要压成 `boolean` / `int`。

## 10. 改动点计数法

新加一个变体后，数一下改动文件：

| 位置 | 期望 |
|---|---|
| 常量（类型码） | 1 |
| 投影（一段 SELECT + 一行 UNION ALL） | 1 |
| 内核算法 | 0 |
| 终止 / 收口逻辑 | 0 |
| 预览 / 试算 | 0 |
| 统计 / 导出 | 0 |

`≥4` 就说明抽象失败，这四处就是下次加变体还要付一遍的账单。

## 11. 内核里不该出现的六样东西

1. Mapper / Repository / 任何 IO
2. `@Transactional` / 事务传播
3. `HttpServletRequest` / `SecurityUtils` / 请求上下文
4. 当前时间（`LocalDate.now()`）—— 时间必须由入参传入
5. 随机数 / UUID（编号生成属于写入点）
6. 日志以外的副作用（写文件、发消息）
