"""ミサイル: 目標を追尾し衝突でダメージを与える移動体。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid
from game.objects.mover import Mover
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.equipment.missile_nav import MissileNavigation

DETONATE_RANGE = 10.0  # grid  起爆距離


class Missile(Mover):
    def __init__(
        self,
        pos: Vec2,
        iff: str,
        power: float,
        speed: float,
        flight_time: float,
        on_report: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(pos, size=0.01, durability=1.0)
        self.iff: str = iff          # "U": 連邦, "K": クリンゴン
        self.power: float = power    # gj
        self.speed = speed           # grid/sec (Mover.speed)
        self.flight_time: float = flight_time  # sec
        self.elapsed: float = 0.0
        self.nav: "MissileNavigation | None" = None
        self._on_report: Callable[[str], None] | None = on_report

    def set_nav(self, nav: "MissileNavigation") -> None:
        self.nav = nav

    def update(self, dt: float) -> None:
        if self.destroyed:
            return
        self.elapsed += dt
        if self.elapsed >= self.flight_time:
            self.destroyed = True
            return

        if self.nav:
            self.nav.update(dt)

        super().update(dt)

    def check_detonation(self, objects: list) -> None:
        """目標の表面から DETONATE_RANGE grid 以内なら起爆する。"""
        if self.destroyed or self.nav is None or self.nav.target is None:
            return
        target = self.nav.target
        if target.destroyed:
            self.destroyed = True
            return
        dist = distance_grid(self.pos, target.pos) - target.size
        if dist <= DETONATE_RANGE:
            hull_dmg = target.receive_damage(self.power)
            self.destroyed = True
            if self._on_report:
                from game.constants import REPORT_ALERT
                shield_absorbed = self.power - hull_dmg
                if shield_absorbed > 0:
                    self._on_report(
                        f"ミサイル命中: {type(target).__name__} "
                        f"シールド{shield_absorbed:.0f}gj吸収 / 艦体{hull_dmg:.0f}gj"
                    )
                else:
                    self._on_report(
                        f"ミサイル命中: {type(target).__name__} に {hull_dmg:.0f}gj ダメージ"
                    )
                if target.destroyed:
                    self._on_report(f"{REPORT_ALERT}{type(target).__name__} 撃沈")
