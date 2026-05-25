"""ミサイルランチャー: ミサイルを管理・発射する。"""
from __future__ import annotations
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.objects.missile import Missile
    from game.equipment.radar import Radar


class MissileLauncher(Equipment):
    def __init__(
        self,
        owner: "Thing",
        capacity: int,
        iff: str,
        missile_power: float,
        missile_speed: float,
        missile_flight_time: float,
        reload_time: float = 0.0,
        on_report: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(owner)
        self.capacity: int = capacity
        self.stock: int = capacity
        self.iff: str = iff
        self.missile_power: float = missile_power
        self.missile_speed: float = missile_speed
        self.missile_flight_time: float = missile_flight_time
        self._reload_time: float = reload_time
        self._reload_remaining: float = 0.0
        self._on_report: Callable[[str], None] | None = on_report
        self._active: list["Missile"] = []  # 発射済みミサイルのリスト

    def update(self, dt: float) -> None:
        if self._reload_remaining > 0.0:
            self._reload_remaining = max(0.0, self._reload_remaining - dt)

    def fire(self, target: "Thing", radar: "Radar") -> "Missile | None":
        """ミサイルを発射して Missile オブジェクトを返す。在庫なし・装填中なら None。"""
        if self._reload_remaining > 0.0:
            if self._on_report:
                self._on_report(f"ミサイル装填中 残り{self._reload_remaining:.1f}秒")
            return None
        if self.stock <= 0:
            if self._on_report:
                self._on_report("ミサイル残弾なし")
            return None
        from game.objects.missile import Missile
        from game.equipment.missile_nav import MissileNavigation
        m = Missile(
            pos=self.owner.pos,
            iff=self.iff,
            power=self.missile_power,
            speed=self.missile_speed,
            flight_time=self.missile_flight_time,
            on_report=self._on_report,
        )
        m.source_id = self.owner.id
        nav = MissileNavigation(m, self.owner, radar)
        nav.set_target(target, self.missile_speed)
        m.set_nav(nav)
        from game.coords import direction_to
        m.heading = direction_to(self.owner.pos, target.pos)
        self.stock -= 1
        self._active.append(m)
        self._reload_remaining = self._reload_time
        if self._on_report:
            self._on_report(f"ミサイル発射 残弾:{self.stock}/{self.capacity}")
        return m

    @property
    def missile_range(self) -> float:
        """ミサイルの最大射程 (grid)。"""
        return self.missile_speed * self.missile_flight_time

    def restock(self) -> None:
        self.stock = self.capacity
