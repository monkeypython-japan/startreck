"""ゲーム終了時のログをマークダウン形式でファイルに書き出す。"""
from __future__ import annotations
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.universe import Universe


def _collect_faction_stats(universe: "Universe", faction: str) -> dict:
    from game.objects.vessel import Vessel

    surviving = [
        o for o in universe.objects
        if isinstance(o, Vessel) and o.faction == faction
    ]
    destroyed = [s for s in universe._destroyed_vessel_stats if s["faction"] == faction]

    vessel_count = len(surviving)

    ml_initial = (
        sum(s["ml_capacity"] for s in destroyed)
        + sum((v.missile_launcher.capacity if v.missile_launcher else 0) for v in surviving)
    )
    ml_fired = (
        sum(s["ml_fired"] for s in destroyed)
        + sum((v.missile_launcher.shots_fired if v.missile_launcher else 0) for v in surviving)
    )
    ml_remaining = sum((v.missile_launcher.stock if v.missile_launcher else 0) for v in surviving)
    ml_unused = ml_initial - ml_fired

    fuel_initial = (
        sum(s["fuel_max"] for s in destroyed)
        + sum((v.generator.fuel_max if v.generator else 0.0) for v in surviving)
    )
    fuel_consumed = (
        sum(s["fuel_consumed"] for s in destroyed)
        + sum((v.generator.fuel_consumed if v.generator else 0.0) for v in surviving)
    )
    fuel_remaining = sum((v.generator.fuel if v.generator else 0.0) for v in surviving)
    fuel_unused = fuel_initial - fuel_consumed

    return {
        "vessel_count": vessel_count,
        "ml_initial": ml_initial,
        "ml_fired": ml_fired,
        "ml_unused": ml_unused,
        "ml_remaining": ml_remaining,
        "fuel_initial": fuel_initial,
        "fuel_consumed": fuel_consumed,
        "fuel_unused": fuel_unused,
        "fuel_remaining": fuel_remaining,
    }


def write_game_log(universe: "Universe", winner: str | None, log_dir: str = ".") -> str:
    """ゲームログをマークダウン形式で書き出し、ファイルパスを返す。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gamelog_{ts}.md"
    filepath = os.path.join(log_dir, filename)

    u = _collect_faction_stats(universe, "U")
    k = _collect_faction_stats(universe, "K")

    if winner == "U":
        winner_label = "連邦（Federation）勝利"
    elif winner == "K":
        winner_label = "クリンゴン（Klingon）勝利"
    else:
        winner_label = "引き分け / ゲーム中断"

    lines = [
        "# Startreck ゲームログ",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 結果",
        "",
        f"- **勝敗**: {winner_label}",
        f"- **経過時間**: {universe.time} 秒",
        "",
        "## 残存艦艇数",
        "",
        "| 勢力 | 残存艦艇数 |",
        "|------|-----------|",
        f"| 連邦 | {u['vessel_count']} |",
        f"| クリンゴン | {k['vessel_count']} |",
        "",
        "## ミサイル統計",
        "",
        "| 勢力 | 初期総数 | 使用数 | 未使用数 | 残存数 |",
        "|------|---------|--------|---------|--------|",
        f"| 連邦 | {u['ml_initial']} | {u['ml_fired']} | {u['ml_unused']} | {u['ml_remaining']} |",
        f"| クリンゴン | {k['ml_initial']} | {k['ml_fired']} | {k['ml_unused']} | {k['ml_remaining']} |",
        "",
        "## 燃料統計",
        "",
        "| 勢力 | 初期総量 (gj) | 使用量 (gj) | 未使用量 (gj) | 残存量 (gj) |",
        "|------|-------------|-----------|-------------|------------|",
        (f"| 連邦 | {u['fuel_initial']:.0f} | {u['fuel_consumed']:.0f} |"
         f" {u['fuel_unused']:.0f} | {u['fuel_remaining']:.0f} |"),
        (f"| クリンゴン | {k['fuel_initial']:.0f} | {k['fuel_consumed']:.0f} |"
         f" {k['fuel_unused']:.0f} | {k['fuel_remaining']:.0f} |"),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return filepath
