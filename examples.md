# 正反例

每组的 `[NN]` 指向 SKILL.md 路由表中的子文档。示例只对照写法，不代表完整业务。

## [01] 枚举分支：不写 default

```java
// 反例：新增枚举值后静默走 default
String name = switch (status) {
    case PAID -> "已支付";
    default -> throw new IllegalStateException("未知状态");
};

// 正例：编译期强制覆盖
String name = switch (status) {
    case CREATED -> "待支付";
    case PAID -> "已支付";
    case CANCELLED -> "已取消";
};
```

## [01] var 的边界

```java
// 反例：读代码看不出类型
var result = orderService.query(param);

// 正例：右侧自明才用 var
var orders = new ArrayList<Order>(10);
var total = BigDecimal.ZERO;

// 正例：类型不自明就写出来
Map<Long, List<Order>> grouped = orderService.groupByUser(param);
```

## [01] 模式匹配替代判断 + 强转

```java
// 反例
if (node instanceof OrderNode) {
    OrderNode order = (OrderNode) node;
    handle(order.id());
}

// 正例
if (node instanceof OrderNode order) {
    handle(order.id());
}
```

## [02] Stream 无副作用

```java
// 反例：forEach 改外部集合，peek 做业务
List<Long> ids = new ArrayList<>();
orders.stream().peek(o -> ids.add(o.id())).count();

// 正例
List<Long> ids = orders.stream().map(Order::id).toList();
```

## [02] toMap 必须给合并函数

```java
// 反例：重复 key 直接抛 IllegalStateException
Map<Long, Order> map = orders.stream()
        .collect(Collectors.toMap(Order::userId, o -> o));

// 正例：保留先出现的一条
Map<Long, Order> map = orders.stream()
        .collect(Collectors.toMap(Order::userId, o -> o, (a, b) -> a));
```

## [02] Map 计数

```java
// 反例
if (!counter.containsKey(status)) {
    counter.put(status, 0L);
}
counter.put(status, counter.get(status) + 1);

// 正例
counter.merge(status, 1L, Long::sum);
```

## [02] Optional 只用于返回值

```java
// 反例：字段与裸 get
private Optional<String> remark;
String text = remark.get();

// 正例：返回值 + 带默认行为
Optional<Order> findById(Long id);           // Service 返回值
String text = findById(id).map(Order::remark).orElse("");
Order order = findById(id).orElseThrow(() -> new BizException(ErrorCode.ORDER_NOT_FOUND));
```

## [02] orElse 与 orElseGet 的区别

```java
// 反例：默认值要查库，却用 orElse 每次先执行
Order order = findById(id).orElse(loadDefaultOrder());

// 正例：惰性求值
Order order = findById(id).orElseGet(() -> loadDefaultOrder());
```

## [03] record 承载查询结果

```java
// 反例：一个只有 getter/setter 的类，只为返回两个字段
public class OrderSummary {
    private Long id;
    private BigDecimal amount;
    // getter / setter ...
}

// 正例
public record OrderSummary(Long id, BigDecimal amount) {
    public OrderSummary {
        Objects.requireNonNull(id);
        Objects.requireNonNull(amount);
    }
}
```

## [03] record 不用于 JPA 实体

```java
// 反例：JPA 需要无参构造与代理
@Entity
public record OrderEntity(Long id, String status) { }

// 正例：实体保持 class，对外用 record 输出
@Entity
@Getter
@Setter
public class OrderEntity {
    @Id
    private Long id;
    private String status;
}

public record OrderView(Long id, String status) {
    public static OrderView of(OrderEntity e) {
        return new OrderView(e.getId(), e.getStatus());
    }
}
```

## [03] Lombok 与实体

```java
// 反例：@Data 生成的 equals/hashCode 触发懒加载、破坏代理
@Data
@Entity
public class Order { }

// 正例
@Getter
@Setter
@Entity
@EqualsAndHashCode(of = "id")
public class Order { }
```

## [04] 时间类型与格式化

```java
// 反例：非线程安全 + 无时区
private static final SimpleDateFormat SDF = new SimpleDateFormat("yyyy-MM-dd");

// 正例
private static final DateTimeFormatter FORMATTER =
        DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

LocalDateTime createdAt = LocalDateTime.now(clock);
String text = createdAt.format(FORMATTER);
```

## [04] BigDecimal 比较与除法

```java
// 反例：equals 比较 scale，除法不给精度
if (a.equals(b)) { }
BigDecimal avg = total.divide(count);

// 正例
if (a.compareTo(b) == 0) { }
BigDecimal avg = total.divide(BigDecimal.valueOf(count), 2, RoundingMode.HALF_UP);
```

## [05] 构造器注入 + 依赖接口

```java
// 反例：字段注入 + 直接依赖第三方实现
@Autowired
private WxPayClient wxPayClient;

// 正例
@Service
@RequiredArgsConstructor
public class PayService {
    private final PayGateway payGateway;   // 业务侧接口，实现可替换
}
```

## [05] 参数对象替代长参数列表

```java
// 反例
List<Order> search(String status, LocalDate start, LocalDate end, Long userId, int page, int size);

// 正例
public record OrderQuery(String status, LocalDate start, LocalDate end, Long userId, int page, int size) {
    public OrderQuery {
        if (page < 1 || size < 1 || size > 100) {
            throw new BizException(ErrorCode.INVALID_PAGE);
        }
    }
}
```

## [06] 策略替代 if-else 链

```java
// 反例：新增渠道就要改这个方法
if ("WX".equals(channel)) {
    wxPay(order);
} else if ("ALI".equals(channel)) {
    aliPay(order);
} else if ("BALANCE".equals(channel)) {
    balancePay(order);
}

// 正例：注册表 key 用枚举 code，新增渠道只加一个实现
public interface PayHandler {
    PayChannel channel();
    void pay(Order order);
}

@Service
@RequiredArgsConstructor
public class PayDispatcher {
    private final Map<PayChannel, PayHandler> handlers;

    public PayDispatcher(List<PayHandler> list) {
        this.handlers = list.stream().collect(Collectors.toMap(PayHandler::channel, h -> h));
    }

    public void dispatch(Order order) {
        PayHandler handler = handlers.get(order.channel());
        if (handler == null) {
            throw new BizException(ErrorCode.UNSUPPORTED_CHANNEL);
        }
        handler.pay(order);
    }
}
```

## [06] 不要为单实现抽接口

```java
// 反例：一个实现、没有替换计划
public interface OrderQueryService { OrderView get(Long id); }
public class OrderQueryServiceImpl implements OrderQueryService { ... }

// 正例：直接一个类；只有外部边界（支付、短信）才抽接口
@Service
public class OrderQueryService { ... }
```

## [07] 线程池必须自建命名与有界队列

```java
// 反例：无界队列 + 无线程名
ExecutorService pool = Executors.newFixedThreadPool(8);

// 正例
ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
executor.setCorePoolSize(8);
executor.setMaxPoolSize(16);
executor.setQueueCapacity(200);
executor.setThreadNamePrefix("order-async-");
executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
executor.initialize();
```

## [07] 异步必须有超时与异常处理

```java
// 反例：无超时、异常被吞
CompletableFuture.supplyAsync(() -> remote.call(id));

// 正例
CompletableFuture<Result> future = CompletableFuture
        .supplyAsync(() -> remote.call(id), executor)
        .orTimeout(3, TimeUnit.SECONDS)
        .exceptionally(e -> {
            log.warn("远程调用失败 id={}", id, e);
            throw new BizException(ErrorCode.REMOTE_FAILED, e);
        });
```

## [07] 事务提交后再发消息

```java
// 反例：事务未提交就发 MQ，回滚后消息已出去
@Transactional
public void pay(Long orderId) {
    orderMapper.updatePaid(orderId);
    mq.send(new OrderPaidEvent(orderId));
}

// 正例
@Transactional
public void pay(Long orderId) {
    orderMapper.updatePaid(orderId);
    publisher.publishEvent(new OrderPaidEvent(orderId));
}

@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onPaid(OrderPaidEvent event) {
    mq.send(event);
}
```

## [08] 参数化 SQL

```xml
<!-- 反例：${} 拼接，可注入 -->
<select id="find" resultType="Order">
    SELECT id, status FROM orders WHERE status = '${status}'
</select>

<!-- 正例：#{} + 列显式 -->
<select id="find" resultMap="OrderMap">
    SELECT id, status, amount FROM orders WHERE status = #{status}
</select>
```

## [08] 循环内查库改批量

```java
// 反例：N+1
for (Order order : orders) {
    User user = userMapper.selectById(order.getUserId());
    order.setUserName(user.getName());
}

// 正例：一次批量取回后映射
Set<Long> userIds = orders.stream().map(Order::getUserId).collect(Collectors.toSet());
Map<Long, User> userMap = userMapper.selectByIds(userIds).stream()
        .collect(Collectors.toMap(User::getId, u -> u));
orders.forEach(o -> o.setUserName(userMap.get(o.getUserId()).getName()));
```

## [08] 缓存三防

```java
// 反例：穿透 + 雪崩（无空值缓存、TTL 统一）
return redis.get(key);

// 正例：空值短缓存 + 随机 TTL + 互斥重建
String cached = redis.get(key);
if (cached != null) {
    return cached.isEmpty() ? null : cached;
}
String value = loadFromDb(id);
long ttl = 300 + ThreadLocalRandom.current().nextLong(30);   // 300–330 秒抖动
redis.set(key, value == null ? "" : value, ttl);
return value;
```

## [09] 异常重抛保留 cause

```java
// 反例：丢堆栈
catch (IOException e) {
    throw new BizException(e.getMessage());
}

// 正例
catch (IOException e) {
    throw new BizException(ErrorCode.FILE_READ_FAILED, e);
}
```

## [09] 日志占位符与脱敏

```java
// 反例：拼接 + 打全量报文 + 丢堆栈
log.info("pay result: " + JSON.toJSONString(req));
log.error("pay failed: " + e.getMessage());

// 正例
log.info("支付结果 orderId={} channel={} success={}", orderId, channel, success);
log.error("支付回调处理失败 orderId={}", orderId, e);
```
