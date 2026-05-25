"""ナビゲーター: 移動目標への航行・回避機動を担当。"""
from __future__ import annotations
import math
from game.coords import Vec2, distance_grid, direction_to, wrap_vec
from game.crew.bridge_crew import BridgeCrew
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel

ARRIVAL_THRESHOLD = 20.0  # grid  これ以内に入ったら到着とみなす


class Navigator(BridgeCrew):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)
        self.destination: Vec2 | None = None
        self._evading: bool = False
        self._evasion_dir: Vec2 = Vec2(0.0, 1.0)
        self._flee_evading: bool = False

    def set_destination(self, pos: Vec2, speed: float | None = None) -> None:
        self._evading = False
        self._flee_evading = False
        self.destination = pos
        self.vessel.set_heading_to(pos)
        if speed is not None:
            self.vessel.set_speed(speed)

    def stop(self) -> None:
        self.destination = None
        self._evading = False
        self._flee_evading = False
        self.vessel.set_speed(0.0)

    def start_evasion(self, threat_dir: Vec2) -> None:
        """脅威方向に直交する向きで最大速度で回避機動開始。"""
        self._evading = True
        self._evasion_dir = threat_dir.perpendicular()
        self.vessel.heading = self._evasion_dir
        self.vessel.set_speed(self.vessel.max_speed)
        self.report("回避機動開始")

    def end_evasion(self) -> None:
        if self._evading:
            self._evading = False
            self.vessel.set_speed(0.0)
            self.report("回避機動終了")

    def update(self, dt: float) -> None:
        if self._flee_evading:
            self._update_flee_direction()
            return
        if self._evading:
            self._check_evasion_end()
            return
        if self.destination is None:
            return
        dist = distance_grid(self.vessel.pos, self.destination)
        if dist <= ARRIVAL_THRESHOLD:
            self.destination = None
            self.vessel.set_speed(0.0)
            self.report("目的地に到着")
        else:
            self.vessel.set_heading_to(self.destination)

    def _check_evasion_end(self) -> None:
        """レーダーに自艦を狙うミサイルがなくなったら回避終了。"""
        from game.objects.missile import Missile
        if self.vessel.radar is None:
            return
        enemy_iff = "K" if self.vessel.faction == "U" else "U"
        threat = any(
            isinstance(c, Missile) and c.iff == enemy_iff
            for c in self.vessel.radar.contacts
        )
        if not threat:
            self.end_evasion()

    # ── 敵密度回避 ─────────────────────────���────────────────────

    def start_flee_evasion(self) -> None:
        """敵密度が最も低い方向へ最大速度で回避行動を開始する。"""
        self._evading = False
        self._flee_evading = True
        self.destination = None
        self._update_flee_direction()
        self.report("回避行動開始")

    def end_flee_evasion(self) -> None:
        if self._flee_evading:
            self._flee_evading = False
            self.vessel.set_speed(0.0)
            self.destination = None
            self.report("回避行動終了: レーダーから敵影なし")
            # コマンダーへ通知
            if self.vessel.bridge and self.vessel.bridge.commander:
                self.vessel.bridge.commander.on_flee_evasion_ended()

    def _update_flee_direction(self) -> None:
        """現在の敵分布から逃走方向を計算して進路・速度を更新する。"""
        if not self.vessel.radar:
            self.end_flee_evasion()
            return
        enemy_faction = "K" if self.vessel.faction == "U" else "U"
        from game.objects.vessel import Vessel as _V
        enemies = [
            c for c in self.vessel.radar.contacts
            if isinstance(c, _V) and c.faction == enemy_faction
        ]
        if not enemies:
            self.end_flee_evasion()
            return

        # 敵の重心方向ベクトルを合計し、その逆方向を逃走方向とする
        fx, fy = 0.0, 0.0
        for e in enemies:
            d = direction_to(self.vessel.pos, e.pos)
            fx += d.x
            fy += d.y
        mag = math.hypot(fx, fy)
        if mag > 0.01:
            flee_dir = Vec2(-fx / mag, -fy / mag)
        else:
            # 全方位から囲まれている場合は最遠の敵と反対側へ
            farthest = max(enemies, key=lambda e: distance_grid(self.vessel.pos, e.pos))
            d = direction_to(self.vessel.pos, farthest.pos)
            flee_dir = Vec2(-d.x, -d.y)

        self.vessel.heading = flee_dir
        self.vessel.set_speed(self.vessel.max_speed)
        # 遠方の目標点を設定（到着チェックを使わず heading で制御）
        self.destination = wrap_vec(Vec2(
            self.vessel.pos.x + flee_dir.x * 3.0,
            self.vessel.pos.y + flee_dir.y * 3.0,
        ))
