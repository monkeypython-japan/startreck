"""ビーム: 先端が進みながら周辺オブジェクトにダメージを与える移動体。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid, direction_to, GRID
from game.objects.mover import Mover
from game.constants import (
    BEAM_FULL_DAMAGE_RANGE,
    BEAM_PARTIAL_DAMAGE_RANGE,
    BEAM_PARTIAL_DAMAGE_RATE,
)
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.objects.thing import Thing


class Beam(Mover):
    def __init__(
        self,
        origin: Vec2,
        heading: Vec2,
        iff: str,
        power: float,
        speed: float,
        max_range: float,
        owner: "Thing | None" = None,
        on_report: Callable[[str], None] | None = None,
        on_hit: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(origin, size=0.0, durability=1.0)
        self.origin: Vec2 = origin
        self.heading = heading.normalized()
        self.speed = speed          # grid/sec
        self.iff: str = iff
        self.power: float = power   # gj
        self.max_range: float = max_range   # grid
        self.traveled: float = 0.0          # grid
        self.owner: "Thing | None" = owner
        self._on_report: Callable[[str], None] | None = on_report
        self._on_hit: Callable[[], None] | None = on_hit

    def update(self, dt: float) -> None:
        if self.destroyed:
            return
        move_grid = self.speed * dt
        self.traveled += move_grid
        if self.traveled >= self.max_range:
            self.destroyed = True
            return
        super().update(dt)

    def check_damage(self, objects: list) -> None:
        """先端周辺のオブジェクトにダメージを与える。ミサイルは即時撃墜。"""
        if self.destroyed:
            return
        from game.objects.star import Star
        from game.objects.missile import Missile
        for obj in objects:
            if obj is self or obj is self.owner:
                continue
            dist = distance_grid(self.pos, obj.pos) - obj.size
            if isinstance(obj, Star):
                if dist <= 0:
                    self.destroyed = True
                    return
                continue
            # ミサイルは無条件撃墜（IFF確認: 敵ミサイルのみ）
            if isinstance(obj, Missile):
                if obj.iff == self.iff:
                    continue
                if dist <= BEAM_FULL_DAMAGE_RANGE:
                    obj.intercepted = True
                    obj.destroyed = True
                    self.destroyed = True
                    if self._on_hit:
                        self._on_hit()
                    if self._on_report:
                        self._on_report("ビームでミサイル撃墜")
                    return
                continue
            if dist <= BEAM_FULL_DAMAGE_RANGE:
                dmg = self.power
            elif dist <= BEAM_PARTIAL_DAMAGE_RANGE:
                dmg = self.power * BEAM_PARTIAL_DAMAGE_RATE
            else:
                continue
            hull_dmg = obj.receive_damage(dmg)
            if self._on_hit:
                self._on_hit()
            if self.owner and hasattr(obj, 'notify_attacked_by'):
                obj.notify_attacked_by(self.owner.id)
            self.destroyed = True
            if self._on_report:
                from game.constants import REPORT_ALERT
                shield_absorbed = dmg - hull_dmg
                if shield_absorbed > 0:
                    self._on_report(
                        f"ビーム命中: {type(obj).__name__} "
                        f"シールド{shield_absorbed:.0f}gj吸収 / 艦体{hull_dmg:.0f}gj"
                    )
                else:
                    self._on_report(
                        f"ビーム命中: {type(obj).__name__} に {hull_dmg:.0f}gj ダメージ"
                    )
                if obj.destroyed:
                    self._on_report(f"{REPORT_ALERT}{type(obj).__name__} 撃沈")
            return
