"""ゲーム終了時のログをマークダウン形式でファイルに書き出す。"""
from __future__ import annotations
import math
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
        sum(s["ml_provided"] for s in destroyed)
        + sum((v.missile_launcher.total_provided if v.missile_launcher else 0) for v in surviving)
    )
    ml_fired = (
        sum(s["ml_fired"] for s in destroyed)
        + sum((v.missile_launcher.shots_fired if v.missile_launcher else 0) for v in surviving)
    )
    ml_remaining = sum((v.missile_launcher.stock if v.missile_launcher else 0) for v in surviving)
    ml_unused = ml_initial - ml_fired

    fuel_initial = (
        sum(s["fuel_provided"] for s in destroyed)
        + sum((v.generator.total_fuel_provided if v.generator else 0.0) for v in surviving)
    )
    fuel_consumed = (
        sum(s["fuel_consumed"] for s in destroyed)
        + sum((v.generator.fuel_consumed if v.generator else 0.0) for v in surviving)
    )
    fuel_remaining = sum((v.generator.fuel if v.generator else 0.0) for v in surviving)
    fuel_unused = fuel_initial - fuel_consumed

    beam_fired = (
        sum(s.get("beam_fired", 0) for s in destroyed)
        + sum((v.beam_launcher.shots_fired if v.beam_launcher else 0) for v in surviving)
    )
    beam_hits = (
        sum(s.get("beam_hits", 0) for s in destroyed)
        + sum((v.beam_launcher.hits if v.beam_launcher else 0) for v in surviving)
    )
    beam_hit_rate = (beam_hits / beam_fired * 100.0) if beam_fired > 0 else 0.0

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
        "beam_fired": beam_fired,
        "beam_hits": beam_hits,
        "beam_hit_rate": beam_hit_rate,
    }


def _vessel_type_label(type_name: str) -> str:
    return {
        "HeavyCruiser": "重巡洋艦",
        "Destroyer": "駆逐艦",
        "GuardDestroyer": "護衛型駆逐艦",
        "SpecialShip": "特務艦",
    }.get(type_name, type_name)


def _collect_vessel_type_losses(universe: "Universe") -> list[dict]:
    """艦種ごとの損失数テーブルを返す。"""
    from game.objects.vessel import Vessel
    from game.vessels.heavy_cruiser import HeavyCruiser
    from game.vessels.destroyer import Destroyer
    from game.vessels.guard_destroyer import GuardDestroyer
    from game.vessels.special_ship import SpecialShip

    type_order = ["HeavyCruiser", "Destroyer", "GuardDestroyer", "SpecialShip"]

    # 生存数を艦種×勢力でカウント
    surviving_count: dict[tuple[str, str], int] = {}
    for o in universe.objects:
        if isinstance(o, Vessel):
            key = (type(o).__name__, o.faction)
            surviving_count[key] = surviving_count.get(key, 0) + 1

    # 損失数を艦種×勢力でカウント
    lost_count: dict[tuple[str, str], int] = {}
    for s in universe._destroyed_vessel_stats:
        key = (s["vessel_type"], s["faction"])
        lost_count[key] = lost_count.get(key, 0) + 1

    rows = []
    for t in type_order:
        u_lost = lost_count.get((t, "U"), 0)
        k_lost = lost_count.get((t, "K"), 0)
        u_surv = surviving_count.get((t, "U"), 0)
        k_surv = surviving_count.get((t, "K"), 0)
        if u_lost + k_lost + u_surv + k_surv == 0:
            continue
        rows.append({
            "type": t,
            "label": _vessel_type_label(t),
            "u_lost": u_lost, "u_surv": u_surv,
            "k_lost": k_lost, "k_surv": k_surv,
        })
    return rows


def _build_event_timeline(universe: "Universe") -> list[str]:
    """ゲームイベントのタイムライン行を返す。"""
    from game.coords import sector

    events: list[tuple[int, str]] = []

    # 最初の艦艇喪失
    for faction, label in (("U", "連邦"), ("K", "クリンゴン")):
        times = [s["destroyed_at"] for s in universe._destroyed_vessel_stats
                 if s["faction"] == faction and "destroyed_at" in s]
        if times:
            events.append((min(times), f"最初の艦艇喪失: {label} @{min(times)}秒"))

    # 基地破壊イベント
    faction_label = {"U": "連邦", "K": "クリンゴン"}
    for ev in universe._destroyed_base_events:
        sx, sy = sector(ev["pos"])
        fl = faction_label.get(ev["faction"], ev["faction"])
        events.append((ev["time"], f"基地破壊 ({fl}) セクタ({sx},{sy}) @{ev['time']}秒"))

    events.sort(key=lambda x: x[0])
    return [f"- {msg}" for _, msg in events]


def _build_initial_base_section(universe: "Universe") -> list[str]:
    """初期基地配置セクションの行を返す。"""
    from game.coords import sector, distance_grid

    lines = [
        "## 初期基地配置",
        "",
        "| 勢力 | 座標 | セクタ |",
        "|------|------|--------|",
    ]
    faction_label = {"U": "連邦", "K": "クリンゴン"}
    by_faction: dict[str, list] = {"U": [], "K": []}
    for b in universe.initial_base_positions:
        by_faction[b["faction"]].append(b["pos"])

    for faction in ("U", "K"):
        for pos in by_faction[faction]:
            sx, sy = sector(pos)
            lines.append(f"| {faction_label[faction]} | ({pos.x:.1f}, {pos.y:.1f}) | ({sx}, {sy}) |")

    lines.append("")
    lines.append("最小基地間距離（toroidal）:")
    for faction in ("U", "K"):
        positions = by_faction[faction]
        if len(positions) >= 2:
            min_d = min(
                distance_grid(positions[i], positions[j])
                for i in range(len(positions))
                for j in range(i + 1, len(positions))
            )
            lines.append(f"- {faction_label[faction]}: {min_d:.0f} grid")

    return lines


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

    ml_use_u = u["ml_fired"] / u["ml_initial"] * 100 if u["ml_initial"] > 0 else 0.0
    ml_use_k = k["ml_fired"] / k["ml_initial"] * 100 if k["ml_initial"] > 0 else 0.0
    fuel_use_u = u["fuel_consumed"] / u["fuel_initial"] * 100 if u["fuel_initial"] > 0 else 0.0
    fuel_use_k = k["fuel_consumed"] / k["fuel_initial"] * 100 if k["fuel_initial"] > 0 else 0.0

    type_rows = _collect_vessel_type_losses(universe)
    timeline_lines = _build_event_timeline(universe)
    base_section_lines = _build_initial_base_section(universe)

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
        "## 艦種別損失",
        "",
        "| 艦種 | 連邦(損失/生存) | クリンゴン(損失/生存) |",
        "|------|----------------|----------------------|",
    ]
    for r in type_rows:
        lines.append(
            f"| {r['label']} | {r['u_lost']} / {r['u_surv']} | {r['k_lost']} / {r['k_surv']} |"
        )

    lines += [
        "",
        "## イベントタイムライン",
        "",
    ]
    lines += timeline_lines if timeline_lines else ["- （イベントなし）"]

    lines += [
        "",
        "## ミサイル統計",
        "",
        "| 勢力 | 累計供給数 | 使用数 | 使用率 | 未使用数 | 残存数 |",
        "|------|----------|--------|--------|---------|--------|",
        (f"| 連邦 | {u['ml_initial']} | {u['ml_fired']} | {ml_use_u:.1f}% |"
         f" {u['ml_unused']} | {u['ml_remaining']} |"),
        (f"| クリンゴン | {k['ml_initial']} | {k['ml_fired']} | {ml_use_k:.1f}% |"
         f" {k['ml_unused']} | {k['ml_remaining']} |"),
        "",
        "## 燃料統計",
        "",
        "| 勢力 | 累計供給量 (gj) | 使用量 (gj) | 使用率 | 未使用量 (gj) | 残存量 (gj) |",
        "|------|--------------|-----------|--------|-------------|------------|",
        (f"| 連邦 | {u['fuel_initial']:.0f} | {u['fuel_consumed']:.0f} | {fuel_use_u:.1f}% |"
         f" {u['fuel_unused']:.0f} | {u['fuel_remaining']:.0f} |"),
        (f"| クリンゴン | {k['fuel_initial']:.0f} | {k['fuel_consumed']:.0f} | {fuel_use_k:.1f}% |"
         f" {k['fuel_unused']:.0f} | {k['fuel_remaining']:.0f} |"),
        "",
        "## ビーム統計",
        "",
        "| 勢力 | 発射回数 | 命中回数 | 命中率 |",
        "|------|---------|---------|-------|",
        f"| 連邦 | {u['beam_fired']} | {u['beam_hits']} | {u['beam_hit_rate']:.1f}% |",
        f"| クリンゴン | {k['beam_fired']} | {k['beam_hits']} | {k['beam_hit_rate']:.1f}% |",
        "",
    ]
    lines += base_section_lines

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return filepath
