# WorkBuddy 专项开发上下文

> 本文档用于 WorkBuddy 专项奖励评选，说明本 Skill 在 WorkBuddy 环境中的使用方式与开发思路。

## 一、Skill 是什么

**McMunch 麦门食光** 是一个面向 AI Agent 的可加载技能包（Skill），核心文件为 `SKILL.md`。它教 Agent 学会调度麦当劳 MCP 的 30+ 个真实业务工具，帮用户完成四类场景：

1. **营养顾问**：按热量 / 蛋白质 / 钠目标智能搭配套餐。
2. **省钱管家**：自动领券、按门店实测用券、积分资产体检。
3. **活动先知**：活动日历 + 主题活动链路推荐。
4. **一键点餐**：从方案直接走到下单闭环。

## 二、在 WorkBuddy 中加载

1. 在 WorkBuddy「连接器（Connector）」中添加麦当劳 MCP：
   - 地址 `https://mcp.mcd.cn`，类型 Streamable HTTP，鉴权头 `Authorization: Bearer <你的Token>`。
   - 参考官方文档：https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector
2. 把 `SKILL.md` 放入 WorkBuddy 技能目录（或直接作为上下文指令加载）。
3. 对话即用：
   - 「帮我配一个 600 千卡以内的高蛋白午餐」
   - 「今天麦当劳有什么优惠，帮我领券」
   - 「帮我点板烧鸡腿堡套餐，到店取」

## 三、开发思路

### 为什么做这个主题
- 麦当劳 MCP 工具多而真实，但普通用户不会用；Skill 的价值是把「会用的 Agent」变成「人人可用的对话能力」。
- 三个真实痛点均有 MCP 工具支撑：营养（`list-nutrition-foods`）、省钱（`auto-bind-coupons` / `query-store-coupons` / `query-my-account`）、活动（`campaign-calendar`）。
- 闭环设计：不只给建议，还能直接下单（`calculate-price` → `create-order`），演示效果好。

### Skill 设计要点
- **意图识别 → 约束收集 → 数据获取 → 方案生成 → 比价验证 → 确认下单** 的六步工作流。
- **四维约束引擎**：热量 / 蛋白质 / 钠 / 预算同时校验，参考实现见 `scripts/mcnutrition.py`。
- **券要实测**：所有优惠券是否可用，以 `query-store-coupons` + `calculate-price` 实测为准，避免 Agent 凭券名猜价。
- **写操作前置确认**：领券、下单、积分兑换均为写操作，必须先展示方案、经用户确认再执行。
- **零 Token 泄露**：配置只用 `${MCD_MCP_TOKEN}` 环境变量占位符。

## 四、演示脚本

`scripts/mcnutrition.py` 是营养搭配引擎的离线参考实现：

```bash
python scripts/mcnutrition.py --goal "650千卡 高蛋白"
python scripts/mcnutrition.py --max-kcal 500 --min-protein 25 --max-sodium 1500 --budget 25
```

脚本内置麦当劳 MCP `list-nutrition-foods` 的真实营养快照（2026-10），可独立演示四维约束搜索与省钱方案模拟；接入真实 MCP 后由 Agent 按 `SKILL.md` 调度实时数据。

## 五、合规

- 本 Skill 为 2026 麦当劳程序员创意开发大赛参赛作品，非麦当劳官方产品。
- 所有配置不含真实 Token / 密钥 / 个人信息，仅使用环境变量占位符。
- 餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。
