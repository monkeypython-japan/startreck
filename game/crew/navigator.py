"""ナビゲーター: 移動目標への航行・回避機動を担当。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid
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

    def set_destination(self, pos: Vec2, speed: float | None = None) -> None:
        self._evading = False
        self.destination = pos
        self.vessel.set_heading_to(pos)
        if speed is not None:
            self.vessel.set_speed(speed)

    def stop(self) -> None:
        self.destination = None
        self._evading = False
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
