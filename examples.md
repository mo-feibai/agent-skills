# 正反例

配合 [SKILL.md](SKILL.md) 使用。所有示例基于 Spring Boot + MyBatis + JDK 17。

## 1. 类注释

**正例**

```java
/**
 * 订单创建与状态流转入口。
 *
 * <p>订单金额以分为单位在内部流转，对外接口统一使用元。
 * 本类线程安全，依赖的仓储为无状态实现。
 *
 * @author Zc
 * @since 2026-09-15
 */
@Service
public class OrderService {
}
```

**反例**

```java
// 订单服务
@Service
public class OrderService {
}
```

问题：用了 `//` 而非 Javadoc（阿里强制）；没有职责说明、创建者、创建日期、线程安全声明；"订单服务"等于重复类名。

## 2. 方法注释

**正例**

```java
/**
 * 创建订单并扣减库存。
 *
 * <p>幂等：同一 {@code requestId} 重复调用返回首次结果，不会重复扣减。
 *
 * @param request 下单请求，{@code requestId} 非空且全局唯一
 * @param operatorId 操作人 ID，用于审计
 * @return 订单 ID，创建失败抛出业务异常
 * @throws InsufficientStockException 库存不足时抛出，错误码 ORDER_STOCK_001
 * @author Zc
 * @since 2026-09-15
 */
public Long createOrder(CreateOrderRequest request, Long operatorId) {
}
```

**反例**

```java
// 创建订单
public Long createOrder(CreateOrderRequest request, Long operatorId) {
}
```

问题：没有参数、返回值、异常、幂等性说明；首句只是复述方法名。

## 3. 字段 / 常量

**正例**

```java
/** 支付超时时间，单位：秒，默认 900 秒（15 分钟），来源：产品文档 v2.3 */
private static final int PAY_TIMEOUT_SECONDS = 900;

/** 订单实付金额，单位：元，保留 2 位小数，非空 */
@NotNull
private BigDecimal payAmount;

/** 支付完成时间（东八区），未支付时为 null */
@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
private LocalDateTime paidAt;
```

**反例**

```java
private static final int TIMEOUT = 900;
private BigDecimal payAmount;
private LocalDateTime paidAt;
```

问题：魔法值与字段都无注释；金额未写单位与精度；时间未写时区，导致前后端与跨时区解析歧义。

## 4. 行内注释

**正例**

```java
// 需求：PRD-2024-001 —— 会员日折扣按实付金额向下取整到分
long discountCent = payAmountCent * 8 / 10;

// 修复：issue #123 —— 上游 SDK 在超时后仍可能回调，此处按 requestId 去重
if (processedIds.contains(requestId)) {
    return;
}
```

**反例**

```java
// 计算折扣
long discountCent = payAmountCent * 8 / 10;

// i 从 0 到 size
for (int i = 0; i < list.size(); i++) {
}
```

问题：第一条只说明"是什么"却不写业务依据与取整口径；第二条是纯复述，应删除。

## 5. DTO / VO

**正例**

```java
/**
 * 下单请求。
 *
 * @author Zc
 * @since 2026-09-15
 */
public class CreateOrderRequest {

    /** 请求幂等号，非空，全局唯一，由调用方生成 */
    @NotBlank
    @Schema(description = "请求幂等号")
    private String requestId;

    /** 收货人手机号，11 位，存储前加密，日志与注释中禁止出现真实值 */
    @Pattern(regexp = "^1\\d{10}$")
    private String phone;

    /** 支付金额，单位：元，保留 2 位小数，最小 0.01 */
    @NotNull
    @DecimalMin("0.01")
    private BigDecimal payAmount;
}
```

**反例**

```java
public class CreateOrderRequest {
    private String requestId;
    @JsonIgnore
    private String phone;
    private BigDecimal payAmount;
}
```

问题：字段无注释；`@JsonIgnore` 未说明原因（脱敏还是兼容）；`requestId` 的校验注解与注释双双缺失；金额单位与精度不明。

## 6. MyBatis / SQL

**正例**

```java
/**
 * 按门店 + 时间范围统计有效订单。
 *
 * @param storeId 门店 ID，非空
 * @param from 起始时间（含），东八区
 * @param to 结束时间（不含），东八区
 * @return 每行包含 status 与订单数；无数据返回空列表
 * @author Zc
 * @since 2026-09-15
 */
List<OrderStatRow> countByStore(@Param("storeId") Long storeId,
                                @Param("from") LocalDateTime from,
                                @Param("to") LocalDateTime to);
```

```xml
<!-- 动态条件：statusList 为空表示不过滤状态，避免 IN () 语法错误 -->
<if test="statusList != null and statusList.size() > 0">
    AND status IN
    <foreach collection="statusList" item="s" open="(" separator="," close=")">#{s}</foreach>
</if>
```

**反例**

```java
List<OrderStatRow> countByStore(Long storeId, LocalDateTime from, LocalDateTime to);
```

```xml
<if test="statusList != null and statusList.size() > 0">
    AND status IN ...
</if>
```

问题：Mapper 方法无参数与返回口径说明；动态 SQL 的"空集合不过滤"这一行为没有注释，维护者极易误改。

## 7. 复杂逻辑

**正例**

```java
/** 费率配置（注入） */
private FeeProperties feeProperties;

/**
 * 按阶梯费率计算手续费。
 *
 * <p>费率与阶梯阈值由运营配置下发（配置 key：fee.tier.*），代码只实现分段累进；
 * 金额以分为单位，避免浮点误差。
 */
public long calcFeeCent(long amountCent) {
    // 前置：amountCent >= 0，由调用方校验

    // 第一档：未超过阈值部分按第一档费率计算（阈值单位：分，费率单位：千分之一）
    long tier1LimitCent = feeProperties.getTier1LimitCent();
    long tier1RatePpm = feeProperties.getTier1RatePpm();
    if (amountCent <= tier1LimitCent) {
        return amountCent * tier1RatePpm / 1000;
    }

    // 超出阈值部分按第二档费率累进，前段仍按第一档
    long tier1FeeCent = tier1LimitCent * tier1RatePpm / 1000;
    long restCent = amountCent - tier1LimitCent;
    return tier1FeeCent + restCent * feeProperties.getTier2RatePpm() / 1000;
}
```

**反例**

```java
public long calcFeeCent(long amountCent) {
    if (amountCent <= 1000000L) {
        return amountCent * 6 / 1000;
    }
    long a = 1000000L * 6 / 1000;
    long b = amountCent - 1000000L;
    return a + b * 5 / 1000;
}
```

问题：费率与阈值写死在代码里且无来源，金额单位与取整口径靠猜；变量命名 `a`、`b` 无意义；无前置条件说明，负数入参行为未定。

## 8. 安全与保密

**正例**

```java
/**
 * 微信支付回调处理。
 *
 * <p>验签密钥由配置中心注入，不落代码与注释；幂等：同一交易号重复回调只处理一次。
 */
@PostMapping("/pay/notify")
public String notify(@RequestBody String body) {
}
```

**反例**

```java
/**
 * 微信支付回调处理。
 *
 * <p>商户号 M10086，API v3 密钥 WXK-2f8a9c，生产回调地址 https://pay.intra.local/notify，
 * 渠道费率 0.6%，T+1 结算。
 */
@PostMapping("/pay/notify")
public String notify(@RequestBody String body) {
}
```

问题：密钥、商户号、内部域名、费率与结算条款写进注释；注释会随代码进入仓库、评审、截图与外包交付，等同公开。业务依据只引编号，密钥由配置注入。

## 9. 详略控制

**正例**

```java
/**
 * 校验版本记录入参并归一化设备清单。
 *
 * <p>全量升级时清空设备清单，避免残留清单混入全量记录；
 * 置空串而非 null：updateById 的 {@code <if test="imei != null">} 会跳过 null。
 */
public void normalize(UpgradeVersionRecord record) {
}
```

**反例**

```java
/**
 * 校验版本记录入参并归一化设备清单。
 *
 * <p>全量升级必须清空设备清单：PC 端把升级类型切回全量后，表单里的 serialNumber
 * 仍会带上残留值，落库会让「部分升级清单」出现在全量记录上造成语义混乱。
 * 置空串而非 null — updateById 的 &lt;if test="imei != null"&gt; 会跳过 null，导致旧清单残留。
 */
public void normalize(UpgradeVersionRecord record) {
}
```

问题：把前端操作路径与业务后果写成整段叙事，维护者需要的"哪里会踩坑"被淹没；操作路径与流程细节属需求文档，注释只留"清空设备清单"与"空串而非 null"两个维护必需的事实。
