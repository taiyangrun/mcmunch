#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
McMunch 麦门食光 —— 麦当劳营养搭配引擎（参考实现）

功能：
  1. 营养-目标双向匹配：在真实麦当劳营养数据上，按「热量上限 / 蛋白质下限 / 钠上限 / 预算上限」
     四维约束搜索最优套餐组合。
  2. 省钱方案模拟：演示如何结合优惠券给出「用券前后」价格对比。

离线可运行（无需 MCP Token）。真实接入时，由 AI Agent 按 SKILL.md 调度
麦当劳 MCP 工具（list-nutrition-foods / query-meals / calculate-price 等）
获取实时数据后，把数据喂给本引擎做组合搜索。

用法示例：
  python mcnutrition.py --goal "600千卡 高蛋白"
  python mcnutrition.py --max-kcal 650 --min-protein 30
  python mcnutrition.py --max-kcal 500 --min-protein 25 --max-sodium 1500 --budget 25
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 营养数据库（摘自麦当劳 MCP list-nutrition-foods 真实返回，2026-10 快照）
# 字段：name, kcal(千卡), protein(g), fat(g), carb(g), sodium(mg)
# ---------------------------------------------------------------------------
NUTRITION_DB = [
    {"name": "巨无霸", "kcal": 513, "protein": 27, "fat": 26, "carb": 42, "sodium": 961},
    {"name": "双层吉士汉堡", "kcal": 429, "protein": 27, "fat": 22, "carb": 31, "sodium": 1017},
    {"name": "培根蔬萃双层牛堡", "kcal": 442, "protein": 24, "fat": 23, "carb": 34, "sodium": 728},
    {"name": "麦辣鸡腿汉堡", "kcal": 485, "protein": 24, "fat": 24, "carb": 42, "sodium": 1208},
    {"name": "板烧鸡腿堡", "kcal": 391, "protein": 23, "fat": 17, "carb": 35, "sodium": 1041},
    {"name": "麦香鸡", "kcal": 369, "protein": 15, "fat": 17, "carb": 39, "sodium": 731},
    {"name": "麦香鱼", "kcal": 325, "protein": 16, "fat": 13, "carb": 35, "sodium": 556},
    {"name": "吉士汉堡包", "kcal": 294, "protein": 16, "fat": 12, "carb": 30, "sodium": 673},
    {"name": "汉堡包", "kcal": 248, "protein": 13, "fat": 8, "carb": 29, "sodium": 492},
    {"name": "原味板烧鸡腿麦满分", "kcal": 246, "protein": 15, "fat": 9, "carb": 25, "sodium": 611},
    {"name": "火腿扒麦满分", "kcal": 261, "protein": 14, "fat": 12, "carb": 24, "sodium": 608},
    {"name": "猪柳麦满分", "kcal": 308, "protein": 16, "fat": 16, "carb": 24, "sodium": 781},
    {"name": "烟肉蛋麦满分", "kcal": 260, "protein": 16, "fat": 10, "carb": 24, "sodium": 483},
    {"name": "猪柳蛋麦满分", "kcal": 387, "protein": 23, "fat": 21, "carb": 25, "sodium": 846},
    {"name": "大脆鸡扒麦满分", "kcal": 361, "protein": 16, "fat": 17, "carb": 35, "sodium": 804},
    {"name": "火腿扒早安营养卷", "kcal": 444, "protein": 16, "fat": 24, "carb": 39, "sodium": 1065},
    {"name": "儿童鱼排堡", "kcal": 269, "protein": 15, "fat": 6, "carb": 36, "sodium": 442},
    {"name": "大薯条", "kcal": 379, "protein": 6, "fat": 16, "carb": 50, "sodium": 216},
    {"name": "中薯条", "kcal": 289, "protein": 4, "fat": 12, "carb": 38, "sodium": 165},
    {"name": "小薯条", "kcal": 210, "protein": 3, "fat": 9, "carb": 28, "sodium": 120},
    {"name": "麦乐鸡5块", "kcal": 213, "protein": 12, "fat": 12, "carb": 13, "sodium": 422},
    {"name": "麦乐鸡4块", "kcal": 170, "protein": 10, "fat": 10, "carb": 11, "sodium": 337},
    {"name": "麦辣鸡翅-2块", "kcal": 224, "protein": 13, "fat": 15, "carb": 9, "sodium": 537},
    {"name": "脆薯饼", "kcal": 146, "protein": 1, "fat": 9, "carb": 14, "sodium": 311},
    {"name": "苹果片", "kcal": 32, "protein": 0, "fat": 0, "carb": 7, "sodium": 0},
    {"name": "小杯玉米杯", "kcal": 53, "protein": 2, "fat": 1, "carb": 7, "sodium": 1},
    {"name": "那么大鸡排", "kcal": 385, "protein": 24, "fat": 21, "carb": 24, "sodium": 996},
    {"name": "圆筒冰淇淋", "kcal": 93, "protein": 2, "fat": 3, "carb": 14, "sodium": 36},
    {"name": "香芋派", "kcal": 232, "protein": 2, "fat": 12, "carb": 28, "sodium": 159},
    {"name": "菠萝派", "kcal": 221, "protein": 2, "fat": 11, "carb": 27, "sodium": 147},
    {"name": "奥利奥麦旋风", "kcal": 266, "protein": 5, "fat": 9, "carb": 40, "sodium": 116},
    {"name": "无糖可口可乐中杯", "kcal": 0, "protein": 0, "fat": 0, "carb": 1, "sodium": 35},
    {"name": "无糖可口可乐小杯", "kcal": 0, "protein": 0, "fat": 0, "carb": 0, "sodium": 25},
    {"name": "可乐中杯", "kcal": 147, "protein": 0, "fat": 0, "carb": 36, "sodium": 0},
    {"name": "可乐小杯", "kcal": 107, "protein": 0, "fat": 0, "carb": 26, "sodium": 7},
    {"name": "纯悦", "kcal": 0, "protein": 0, "fat": 0, "carb": 0, "sodium": 0},
    {"name": "纯牛奶（盒装）", "kcal": 129, "protein": 7, "fat": 7, "carb": 10, "sodium": 73},
    {"name": "100%苹果汁", "kcal": 88, "protein": 0, "fat": 0, "carb": 21, "sodium": 0},
    {"name": "热美式小杯", "kcal": 10, "protein": 1, "fat": 0, "carb": 1, "sodium": 6},
    {"name": "冰美式小杯", "kcal": 10, "protein": 1, "fat": 0, "carb": 1, "sodium": 6},
    {"name": "鲜萃咖啡小杯", "kcal": 15, "protein": 1, "fat": 0, "carb": 3, "sodium": 2},
    {"name": "锡兰红茶", "kcal": 2, "protein": 0, "fat": 0, "carb": 0, "sodium": 0},
    {"name": "优品豆浆小杯", "kcal": 151, "protein": 6, "fat": 3, "carb": 25, "sodium": 32},
]

MAIN = ["巨无霸", "双层吉士汉堡", "培根蔬萃双层牛堡", "麦辣鸡腿汉堡", "板烧鸡腿堡", "麦香鸡",
        "麦香鱼", "吉士汉堡包", "汉堡包", "原味板烧鸡腿麦满分", "火腿扒麦满分", "猪柳麦满分",
        "烟肉蛋麦满分", "猪柳蛋麦满分", "大脆鸡扒麦满分", "火腿扒早安营养卷", "儿童鱼排堡"]
SNACK = ["大薯条", "中薯条", "小薯条", "麦乐鸡5块", "麦乐鸡4块", "麦辣鸡翅-2块", "脆薯饼",
         "苹果片", "小杯玉米杯", "那么大鸡排"]
DRINK = ["无糖可口可乐中杯", "无糖可口可乐小杯", "可乐中杯", "可乐小杯", "纯悦", "纯牛奶（盒装）",
         "100%苹果汁", "热美式小杯", "冰美式小杯", "鲜萃咖啡小杯", "锡兰红茶", "优品豆浆小杯"]
SWEET = ["圆筒冰淇淋", "香芋派", "菠萝派", "奥利奥麦旋风"]


@dataclass
class Combo:
    """一套组合方案"""
    items: list = field(default_factory=list)

    @property
    def kcal(self) -> int:
        return sum(i["kcal"] for i in self.items)

    @property
    def protein(self) -> float:
        return round(sum(i["protein"] for i in self.items), 1)

    @property
    def fat(self) -> float:
        return round(sum(i["fat"] for i in self.items), 1)

    @property
    def sodium(self) -> int:
        return sum(i["sodium"] for i in self.items)

    def summary(self) -> str:
        parts = []
        for i in self.items:
            parts.append(f"{i['name']}({i['kcal']}千卡/{i['protein']}g蛋白/{i['sodium']}mg钠)")
        return " + ".join(parts)


def parse_goal(text: str) -> dict:
    """从自然语言里解析四维约束，如 '600千卡 高蛋白' '30g蛋白 钠1500'"""
    goal = {}
    m = re.search(r"(\d{2,4})\s*千?卡", text)
    if m:
        goal["max_kcal"] = int(m.group(1))
    m = re.search(r"(\d{1,3})\s*g\s*蛋白", text)
    if m:
        goal["min_protein"] = int(m.group(1))
    m = re.search(r"钠\s*(\d{3,4})", text)
    if m:
        goal["max_sodium"] = int(m.group(1))
    m = re.search(r"(\d{1,3})\s*元", text)
    if m:
        goal["budget"] = int(m.group(1))
    if "高蛋白" in text or "增肌" in text:
        goal["min_protein"] = max(goal.get("min_protein", 0), 30)
    if "减脂" in text or "轻食" in text:
        goal["max_kcal"] = min(goal.get("max_kcal", 9999), 500)
        goal["max_sodium"] = min(goal.get("max_sodium", 99999), 1600)
    return goal


def search_combos(goal: dict, top_n: int = 3) -> list:
    """四维约束组合搜索：1 主食 + 0-2 小食 + 0-1 饮品（可选甜品）。"""
    mains = [i for i in NUTRITION_DB if i["name"] in MAIN]
    snacks = [i for i in NUTRITION_DB if i["name"] in SNACK]
    drinks = [i for i in NUTRITION_DB if i["name"] in DRINK]
    sweets = [i for i in NUTRITION_DB if i["name"] in SWEET]

    max_kcal = goal.get("max_kcal", 9999)
    min_protein = goal.get("min_protein", 0)
    max_sodium = goal.get("max_sodium", 99999)
    budget = goal.get("budget", 40)

    candidates = []
    for main in mains:
        for snack_count in (0, 1, 2):
            for snack_combo in itertools.combinations(snacks, snack_count):
                for drink_count in (0, 1):
                    for drink_combo in itertools.combinations(drinks, drink_count):
                        for sweet_count in (0, 1):
                            for sweet_combo in itertools.combinations(sweets, sweet_count):
                                items = [main, *snack_combo, *drink_combo, *sweet_combo]
                                combo = Combo(items=items)
                                if combo.kcal > max_kcal:
                                    continue
                                if combo.protein < min_protein:
                                    continue
                                if combo.sodium > max_sodium:
                                    continue
                                est_price = 15 + 7 * snack_count + (6 if drink_count else 0) + (8 if sweet_count else 0)
                                if est_price > budget:
                                    continue
                                score = (
                                    combo.protein * 10
                                    - abs(combo.kcal - min(combo.kcal, max_kcal)) * 0.02
                                    - combo.sodium * 0.005
                                )
                                candidates.append((score, combo))

    candidates.sort(key=lambda x: (-x[0], x[1].kcal))
    seen = set()
    unique = []
    for _, combo in candidates:
        key = tuple(sorted(i["name"] for i in combo.items))
        if key in seen:
            continue
        seen.add(key)
        unique.append(combo)
        if len(unique) >= top_n * 2:
            break
    return unique[:top_n]


def demo_coupon_saving(items_price: float, coupons: list) -> dict:
    """省钱方案模拟：给定原价和可用券，输出用券后最省组合。"""
    best = {"original": items_price, "save": 0.0, "used": None, "final": items_price}
    for c in coupons:
        d = c.get("discount", 0)
        p = c.get("percent", 1.0)
        final = items_price - d if d else items_price * p
        final = max(0.0, round(final, 2))
        if items_price - final > best["save"]:
            best = {"original": items_price, "save": round(items_price - final, 2),
                    "used": c["title"], "final": final}
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description="McMunch 麦门食光 · 营养搭配引擎")
    parser.add_argument("--goal", type=str, default="", help='自然语言目标，如 "600千卡 高蛋白"')
    parser.add_argument("--max-kcal", type=int, default=0, help="热量上限（千卡）")
    parser.add_argument("--min-protein", type=int, default=0, help="蛋白质下限（克）")
    parser.add_argument("--max-sodium", type=int, default=0, help="钠上限（mg）")
    parser.add_argument("--budget", type=int, default=0, help="预算上限（元）")
    parser.add_argument("--top", type=int, default=3, help="返回方案数")
    args = parser.parse_args()

    goal = parse_goal(args.goal) if args.goal else {}
    if args.max_kcal:
        goal["max_kcal"] = args.max_kcal
    if args.min_protein:
        goal["min_protein"] = args.min_protein
    if args.max_sodium:
        goal["max_sodium"] = args.max_sodium
    if args.budget:
        goal["budget"] = args.budget
    if not goal:
        goal = {"max_kcal": 700, "min_protein": 25}

    print("=" * 60)
    print("McMunch 麦门食光 · 营养搭配方案")
    print("约束:", json.dumps(goal, ensure_ascii=False))
    print("=" * 60)

    combos = search_combos(goal, top_n=args.top)
    if not combos:
        print("未找到满足全部约束的组合，请放宽热量/钠上限或预算。")
        return 1

    for idx, combo in enumerate(combos, 1):
        print(f"\n方案{idx}（{combo.kcal}千卡 / 蛋白{combo.protein}g / 脂肪{combo.fat}g / 钠{combo.sodium}mg）")
        print("  ", combo.summary())
        ok = (combo.kcal <= goal.get("max_kcal", 9999)
              and combo.protein >= goal.get("min_protein", 0)
              and combo.sodium <= goal.get("max_sodium", 99999))
        print("   状态:", "达标" if ok else "部分约束未满足")

    print("\n" + "-" * 60)
    print("省钱方案模拟（示例券）")
    coupons = [
        {"title": "免费脆薯饼", "discount": 7.5},
        {"title": "薯薯任选", "discount": 8.0},
        {"title": "9.9元中杯冰美式", "discount": 6.0},
    ]
    saving = demo_coupon_saving(31.5, coupons)
    print(f"  原价 {saving['original']} 元 → 使用「{saving['used']}」→ 实付 {saving['final']} 元（省 {saving['save']} 元）")

    print("\n提示：真实使用请接入麦当劳 MCP，由 Agent 按 SKILL.md 获取实时菜单与券数据。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
