# VoIP-Calc-Core 设计文档 — Exam 版

## 限界上下文与模块隔离

费率计算引擎被设计为一个**纯粹的、无状态、无副作用的领域核心**。

### 零依赖策略

核心包 `voip_calc_core.domain` 不引入任何框架依赖：

- **无 Spring/DI 容器**：三条计费规则的组合是简单的管道（Pipeline），不需要策略模式或依赖注入容器。硬编码管道在一览性和可维护性上优于配置文件驱动。
- **无数据库连接**：费率计算是纯函数——输入 CallContext，输出 Money。幂等、持久化、审计日志属于应用层职责，不在领域核心中。
- **无 HTTP/RPC 客户端**：客户身份（VIP/NORMAL）的解析发生在核心之外（应用层或调用方），领域模型只接收已确定的 CustomerTier 值对象。

**决策权衡**：将 tier 放入 CallContext 而非在引擎内部解析，是因为"客户身份解析"涉及外部系统调用（如 Redis、账户微服务），将其留在领域核心会破坏无状态纯函数的属性。代价是调用方需多一次查询——但换来了核心的完全可测试性（无需 mock 外部依赖）。

## 精度与时区防御

### IEEE 754 浮点精度消除

核心计算管线全程使用 `Decimal`，**绝迹 `float` 和 `double`**：

| 隐患 | 防御措施 |
|---|---|
| `float` 直接构造 Decimal | `__post_init__` 拦截非 Decimal 输入，强制 `Decimal(str(value))` 路径 |
| `float * Money` 精度污染 | `__mul__` 检测 float 类型后走 `Decimal(str(scalar))`，隔绝二进制近似 |

**为什么不用整数（分）**：电信计费中间计算涉及 `0.045 * 1.333...` 这类无限小数，整数截断会在管道中间积累误差。全程 Decimal 延迟到最终舍入是行业标准做法。

### 时区漂移防御

`CallContext` 在构造阶段强制校验时区感知性：

```python
def __post_init__(self):
    if self.call_time.tzinfo is None:
        raise ValueError("call_time must be timezone-aware")
```

**设计理由**：不静默假设 UTC 或系统默认时区。一旦 naive datetime 被注入计费核心，服务器物理时区变更（如从上海迁到新加坡）会导致夜间低谷判定系统性偏移 1-2 小时，产生财务对账差异。

## 领域不变量

| 不变量 | 实施位置 |
|---|---|
| 费率 >= 0 | `Money.at_least(Money(0, CNY))` — 最终防线 |
| E.164 格式 | `CountryCode._PATTERN = r"^\+\d+$"` |
| 时区感知 | `CallContext.__post_init__` tzinfo 非空校验 |
| 折扣因子 > 0 | 构造函数隐式保证（枚举内定值） |
| 夜间时间合法 | `NightValleyDiscount.__post_init__` 0-23 范围校验 |

## 架构演进路线

### 当前状态：模块化单体

适合日均 < 10 万次调用的场景。纯内存计算，单次 `calculate()` 耗时 < 0.1ms。

### 高并发演进（生产级展望）

若面临每秒万级 CPS（Calls Per Second），建议分三步演进：

**阶段 1：无状态水平扩展**
RateCalculator 是无状态纯函数，天然支持多实例部署。前置负载均衡（如 Nginx/Envoy），后接 Redis 做客户身份缓存，即可线性扩展至 100k CPS。

**阶段 2：事件驱动异步计费**
引入 Kafka/Plusar 作为呼叫事件总线：
```
CALL_STARTED event -> [RateCalculator] -> CALL_RATED event -> [BillingWriter]
```
计费引擎消费 `CALL_STARTED` 事件，实时计算费率，发布 `CALL_RATED` 事件。计费写入服务独立消费，支持背压和批量写入。

**阶段 3：实时预付费与会话强拆**
在事件驱动架构上叠加实时余额检查：
```
CALL_STARTED -> [RateCalculator] -> [BalanceCheck] -> (余额不足) -> [SessionTerminate]
```
余额检查需在 < 50ms 内完成，避免增加呼叫建立延迟。可引入 Redis 的 `DECR` 原子操作做实时扣费，`INCR` 做挂断后退还未用时长。

**不做的**：本引擎不引入 Flink/Spark Streaming 做流式对账。流式对账属于计费后的批处理分析场景，与实时费率计算是不同限界上下文。
