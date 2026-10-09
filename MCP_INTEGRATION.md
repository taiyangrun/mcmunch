# MCP 接入指南

本项目基于麦当劳中国官方 MCP 服务开发。接入前请先申请自己的 MCP Token。

## 1. 申请 Token

1. 打开 [https://open.mcd.cn/mcp](https://open.mcd.cn/mcp)，点击右上角【登录】。
2. 使用手机号验证登录，进入控制台。
3. 点击【激活】按钮，同意服务协议后即可获得 MCP Token。

## 2. 接入配置

- **接入地址**：`https://mcp.mcd.cn`
- **协议**：Streamable HTTP
- **鉴权**：`Authorization: Bearer YOUR_MCP_TOKEN`

复制仓库中的 [`mcp-config.example.json`](mcp-config.example.json)，将 `${MCD_MCP_TOKEN}` 替换为你的真实 Token 后导入 MCP Client。

## 3. 支持的 MCP 工具

McMunch 主要调度以下工具（完整清单见 [麦当劳 MCP Server README](https://github.com/M-China/mcd-mcp-server)）：

| 能力域 | 工具 |
| --- | --- |
| 营养 | `list-nutrition-foods` |
| 门店 | `query-nearby-stores`（到店/得来速）、`delivery-query-addresses`、`delivery-query-stores`（外送） |
| 菜单 | `query-meals`、`query-meal-detail` |
| 点餐 | `calculate-price`、`create-order`、`cancel-order`、`query-order`、`order-list` |
| 优惠券 | `available-coupons`、`auto-bind-coupons`、`query-my-coupons`、`query-store-coupons` |
| 积分/商城 | `query-my-account`、`mall-points-products`、`mall-product-detail`、`mall-create-order` |
| 活动 | `campaign-calendar`、`query-party-city/store/date/session`、`party-order-create` |
| 其他 | `now-time-info`、`query-lottery-info`、`draw-lottery`、`query-my-prizes` |

## 4. 常用参数速查

| 场景 | 关键参数 |
| --- | --- |
| 到店自取 | `beType=1`，`orderType=1`，不传 `beCode` |
| 得来速 | `beType=5`，`orderType=1`，必传 `beCode`（来自 `query-nearby-stores`） |
| 麦乐送 | `beType=2`，`orderType=2`，必传 `beCode`（来自 `delivery-query-stores`） |
| 企业团餐 | `beType=6`，`orderType=2`，必传 `beCode` 与 `gmServiceCode` |
| 预约 | 所有场景可传 `reservationDate`，格式 `yyyy-MM-dd HH:mm` |
| 价格单位 | `calculate-price` 返回金额单位为**分**，展示时除以 100 转元 |

## 5. 错误码

| code | 原因 | 处理建议 |
| --- | --- | --- |
| 401 | Token 无效、已过期或未提供 | 检查 Authorization 请求头和 Token 配置 |
| 429 | 触发限流（超过 600 次/分钟） | 降低请求频率，合理控制调用间隔 |

## 6. 安全须知

- **Token 严禁提交到仓库**：本仓库所有配置只使用 `${MCD_MCP_TOKEN}` 环境变量占位符，请勿替换为真实 Token 后提交。
- 请妥善保管 MCP Token，避免泄露给他人。
- 使用麦当劳 MCP 服务须遵守麦当劳中国的《使用条款》及《麦当劳 MCP 服务规则》。
