# VoIP-Calc-Core — 跨境 VoIP 费率计算引擎 (Exam 版)

## 题目贴合度

严格按题目要求实现 `calculateRate(CallContext context)` 接口，三条可叠加规则：

```
最终每分钟单价 = max(0, 基础费率 * 客户折扣 - 夜间减免)
```

- 规则 1：国家基础费率（+86=0.10, +1=0.05, 默认=0.50）
- 规则 2：客户折扣（VIP=9 折, NORMAL=无折扣）
- 规则 3：夜间减免（23:00-05:00, -0.02, 下限 0）

## 代码洁癖细节

### 原生类型迷恋的彻底消灭

核心方法 `calculate()` 的入参和返回值中绝迹 `str`/`float`/`int` 原生类型：

```python
def calculate(self, context: CallContext) -> Money:
```

所有数值由值对象内部重载运算符承载，调用方无法在外部进行非法的数学运算。

### 冗余上下文的消除

- `Duration.seconds` 而非 `duration_seconds` — 类名已提供充足语义
- `Money.amount` 而非 `money_amount`
- 模块级变量 `_BASE_RATES` 而非 `COUNTRY_CODE_BASE_RATES`

### 全链路 Decimal 精度

`__mul__` 对 `float` 类型走 `Decimal(str(scalar))` 间接路径，隔绝对二进制近似值的精度污染。全程高精度运算，仅在最终边界舍入。

### Fail-Fast 初始化即自验证

所有值对象在 `__post_init__` 中执行构造期校验，无效状态无法在运行时驻留：

- `Money`: 非 Decimal 输入强制转换
- `CountryCode`: 正则校验 E.164 格式
- `CallContext`: 拒绝 naive datetime
- `NightValleyDiscount`: 小时范围 0-23 校验

## 如何主导 AI 完成高质量交付

1. **架构约束先行**：在 Prompt 中明确"核心必须是无状态纯函数、零框架依赖"，AI 不会主动收敛到这个方向
2. **逐层递进审查**：先检查类型安全（有无 float/double 泄漏），再检查领域建模（值对象是否完备），最后检查边界条件
3. **拒绝过度工程**：AI 倾向于生成 Factory/Strategy/Builder 模式——在 3 条规则的场景下这些都是垃圾代码，一律删除
4. **Prompt 留痕**：见 PROMPTS.md，记录了每一轮"审计指令 → AI 代码脆弱性 → 强制修正"的完整过程

## 技术栈

- Python 3.9
- 零外部依赖（仅标准库）
- 68 个单元测试，0.32s 全绿
