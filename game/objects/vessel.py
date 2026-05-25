"""艦艇: 武装・装備を持つ移動体。"""
from __future__ import annotations
from game.coords import Vec2
from game.objects.mover import Mover
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.equipment.generator import Generator
    from game.equipment.shield import Shield
    from game.equipment.radar import Radar
    from game.equipment.integrator import Integrator
    from game.equipment.bridge import Bridge
    from game.equipment.missile_launcher import MissileLauncher
    from game.equipment.beam_launcher import BeamLauncher
    from game.equipment.jump_drive import JumpDrive


class Vessel(Mover):
    def __init__(
        self,
        pos: Vec2,
        size: float,
        durability: float,
        max_speed: float,
        faction: str,
        supply_provider: bool = False,
    ) -> None:
        super().__init__(pos, size, durability)
        self.max_speed: float = max_speed
        self.faction: str = faction        # "U": 連邦, "K": クリンゴン
        self.supply_provider: bool = supply_provider
        self.supplying: bool = False
        self.supply_timer: float = 0.0
        self.universe = None
        self.messages: list[str] = []

        # 装備 (サブクラスが _init_equipment() で初期化)
        self.generator: Generator | None = None
        self.shield: Shield | None = None
        self.radar: Radar | None = None
        self.integrator: Integrator | None = None
        self.bridge: Bridge | None = None
        self.missile_launcher: MissileLauncher | None = None
        self.beam_launcher: BeamLauncher | None = None
        self.jump_drive: JumpDrive | None = None

    def _report(self, msg: str) -> None:
        self.messages.append(msg)

    def _init_equipment(
        self,
        capacitor_max: float,
        rate_max: float,
        fuel_max: float,
        shield_max_defense: float,
        shield_recovery_rate: float,
        shield_recovery_cost: float,
        shield_deploy_cost: float,
        radar_range: float,
        missile_capacity: int,
        missile_power: float,
        missile_speed: float,
        missile_flight_time: float,
        beam_power: float,
        beam_speed: float,
        beam_range: float,
        missile_reload_time: float = 0.0,
    ) -> None:
        from game.equipment.generator import Generator
        from game.equipment.shield import Shield
        from game.equipment.radar import Radar
        from game.equipment.integrator import Integrator
        from game.equipment.bridge import Bridge
        from game.equipment.missile_launcher import MissileLauncher
        from game.equipment.beam_launcher import BeamLauncher

        self.integrator = Integrator(self)
        self.generator = Generator(self, capacitor_max=capacitor_max,
                                   rate_max=rate_max, fuel_max=fuel_max)
        self.shield = Shield(self, max_defense_energy=shield_max_defense,
                             recovery_rate=shield_recovery_rate,
                             recovery_energy_cost=shield_recovery_cost,
                             deploy_energy_cost=shield_deploy_cost)
        self.radar = Radar(self, scan_range=radar_range, integrator=self.integrator)
        self.missile_launcher = MissileLauncher(
            self, capacity=missile_capacity, iff=self.faction,
            missile_power=missile_power, missile_speed=missile_speed,
            missile_flight_time=missile_flight_time,
            reload_time=missile_reload_time, on_report=self._report,
        )
        self.beam_launcher = BeamLauncher(
            self, iff=self.faction,
            beam_power=beam_power, beam_speed=beam_speed, beam_range=beam_range,
            on_report=self._report,
        )
        self.bridge = Bridge(self, self.radar)

    def notify_attacked_by(self, attacker_id: str) -> None:
        if self.bridge and self.bridge.commander:
            self.bridge.commander.on_attacked_by(attacker_id)

    def receive_damage(self, amount: float) -> float:
        original = amount
        if self.shield is not None and self.shield.current_rate > 0:
            amount = self.shield.absorb(amount)
        hull_dmg = super().receive_damage(amount)
        if hull_dmg > 0 and self.bridge and self.bridge.gunner:
            self.bridge.gunner.report_hit(hull_dmg, original - hull_dmg)
        return hull_dmg

    def set_speed(self, new_speed: float) -> None:
        new_speed = max(0.0, min(new_speed, self.max_speed))
        cost = abs(new_speed - self.speed)
        if cost > 0:
            if self.generator:
                if self.generator.capacitor < cost:
                    return  # エネルギー不足: 速度変更不可
                self.generator.request_energy(cost)
        self.speed = new_speed

    def supply_full(self) -> None:
        """補給を受けて満載状態にする（ダメージ回復・燃料・ミサイル）。"""
        self.damage = 0.0
        if self.generator:
            self.generator.refuel()
            self.generator.recharge()
        if self.missile_launcher:
            self.missile_launcher.restock()
        if self.shield:
            self.shield.current_rate = self.shield.set_rate

    def update(self, dt: float) -> None:
        if self.destroyed:
            return
        if self.universe and self.radar:
            self.radar.scan(
                [o for o in self.universe.objects if o is not self],
                self.universe.time,
            )
        if self.bridge:
            if self.bridge.navigator:
                self.bridge.navigator.update(dt)
            if self.bridge.gunner:
                self.bridge.gunner.update(dt)
        super().update(dt)
        if self.missile_launcher:
            self.missile_launcher.update(dt)
        if self.generator:
            self.generator.update(dt)
        if self.shield and self.generator:
            self.shield.update(dt, self.generator)
