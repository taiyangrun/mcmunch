# McMunch 麦门食光

> 会算热量、会省钱、会帮你点单的麦当劳智能膳食管家 —— 一个基于麦当劳 MCP 的 Agent Skill。

McMunch 把「营养搭配 + 省钱攻略 + 活动先知 + 一键点餐」整合成一个可加载的 Agent Skill。任何支持 MCP 的 AI 助手（WorkBuddy / Cherry Studio / Cursor / Trae / VSCode Copilot）接入麦当劳 MCP 后，加载本 Skill 即可学会四件事：

| 能力 | 一句话说明 | 依赖 MCP 工具 |
| --- | --- | --- |
| 营养顾问 | 按热量 / 蛋白质 / 钠目标自动搭配达标套餐 | `list-nutrition-foods`, `query-meals`, `calculate-price` |
| 省钱管家 | 自动领券、算清每张券怎么用最省、看积分会不会过期 | `available-coupons`, `auto-bind-coupons`, `query-my-coupons`, `query-store-coupons`, `query-my-account` |
| 活动先知 | 把当月营销活动、联名新品、主题活动讲给你听 | `campaign-calendar`, `query-party-*` |
| 一键点餐 | 从推荐方案直接走到下单闭环 | `query-nearby-stores`, `query-meals`, `query-meal-detail`, `calculate-price`, `create-order` |

## 为什么是 McMunch

麦当劳 MCP 提供了 30+ 个真实业务工具，但普通用户面对「菜单 + 优惠券 + 积分 + 活动」时依然有三个真实痛点：

1. **吃怕了**：想控制热量 / 增肌减脂，但不知道麦当劳哪个组合能达标，菜单上也不标热量。
2. **省不动**：麦麦省券、卡包券、门店券散落多处，记不住哪张能用、哪张快过期；积分悄悄过期。
3. **不知道吃啥**：新品、联名、活动日历在 APP 里层层折叠，用户往往错过「9.9 元早餐」「联名」这类限时福利。

McMunch 把这三件事用一套自然语言流程串起来：**你说目标，它给方案，顺带把钱和积分都算明白。**

## 快速开始

### 1. 接入麦当劳 MCP

参考 [`MCP_INTEGRATION.md`](MCP_INTEGRATION.md)，在 MCP Client 中导入 `mcp-config.example.json`（记得把 `${MCD_MCP_TOKEN}` 换成你在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请的 Token）。

### 2. 加载 Skill

- **WorkBuddy / 支持 Agent Skills 的客户端**：把 `SKILL.md` 放入技能的 `skills/` 目录，或直接粘贴到对话上下文。
- **Cursor / Trae**：把 `SKILL.md` 内容作为项目规则文件（`.cursor/rules` / `.trae/rules`）即可。
- **Cherry Studio / 其他**：将 `SKILL.md` 作为系统提示词片段使用。

### 3. 开聊

```
你：我晚饭想控制在 600 千卡以内，蛋白质尽量多，帮我配一套。
McMunch：为您推荐「板烧鸡腿堡 + 麦乐鸡5块 + 无糖可乐中杯」……
```

```
你：帮我看看今天有什么券可以用，怎么点最省？
McMunch：检测到您有「免费脆薯饼（可领）」「人气麦旋风买一送一（可领）」……
```

## 目录结构

```
mcmunch/
├── SKILL.md                  # Agent Skill 定义（核心，加载即用）
├── scripts/
│   └── mcnutrition.py        # 参考实现：营养搭配引擎 + 省钱计算 demo
├── README.md
├── MCP_INTEGRATION.md        # MCP 接入与工具说明
├── mcp-config.example.json   # 脱敏配置模板（环境变量占位符）
├── workbuddy.md              # WorkBuddy 专项开发上下文
└── CONTEST_DECLARATION.md    # 参赛声明
```

## 场景示例

### 营养顾问

```
你：明天想增肌，午餐要吃 40g 蛋白质、热量别超 700 千卡。
McMunch：推荐「双层吉士汉堡(429千卡/27g蛋白) + 麦乐鸡4块(170千卡/10g蛋白) + 纯牛奶(129千卡/7g蛋白)」
        合计 728 千卡 / 44g 蛋白，超预算 28 千卡，可把纯牛奶换成无糖可乐（-129千卡）→ 599 千卡 / 37g 蛋白。
```

### 省钱管家

```
你：帮我领券，然后看看今天吃板烧鸡腿堡怎么最划算。
McMunch：已自动领取「免费脆薯饼」「人气麦旋风买一送一」「9.9元中杯冰美式」。
        当前卡包还有「麦旋风任选」可用。您本月可用积分 208.8，下月无过期风险。
```

### 活动先知

```
你：最近麦当劳有什么活动？
McMunch：10 月进行中：「韩式风味蘸酱上新」「麦当劳 X PEACEMINUSONE 联名」「9.9元早餐两件套」……
```

### 一键点餐

```
你：就按推荐的来，我在 XX 路附近，到店取。
McMunch：已为您选择附近门店 → 计算价格（含最优券）→ 生成订单，请通过支付链接完成支付。
```

## 技术亮点

- **营养-目标双向匹配引擎**：支持「热量上限」「蛋白质下限」「钠上限」「预算上限」四维约束的套餐搜索（见 `scripts/mcnutrition.py`）。
- **券-餐品-门店三层校验**：先用卡包券兜底，再用门店券按订单类型过滤，最后用 `calculate-price` 实测总价，避免「券看着能用、下单时用不了」。
- **积分资产体检**：自动提示本月 / 下月到期积分，避免积分静默过期。
- **零 Token 泄露**：仓库所有配置仅使用 `${MCD_MCP_TOKEN}` 环境变量占位符。

## 开发

```bash
# 离线演示营养搭配引擎（无需 Token）
python scripts/mcnutrition.py --goal "600千卡 高蛋白"

# 完整模式：接入真实 MCP 后由 Agent 依 SKILL.md 调度
```

## 声明

本项目为 **2026 麦当劳程序员创意开发大赛** 参赛作品，非麦当劳官方产品。项目输出仅供参考，不构成医疗、营养或其他专业建议；餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。
