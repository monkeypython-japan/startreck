"""重巡洋艦: クリンゴン艦隊の旗艦。補給提供フラグあり。"""
from __future__ import annotations
from game.coords import Vec2
from game.objects.vessel import Vessel
from game.constants import HEAVY_CRUISER, MISSILE_STANDARD, BEAM_STANDARD, SHIELD_STANDARD, MISSILE_RELOAD_TIME


class HeavyCruiser(Vessel):
    def __init__(self, pos: Vec2, faction: str) -> None:
        p = HEAVY_CRUISER
        super().__init__(
            pos=pos, size=p["size"], durability=p["durability"],
            max_speed=p["max_speed"], faction=faction,
            supply_provider=p["supply_provider"],
        )
        ms, bs, ss = MISSILE_STANDARD, BEAM_STANDARD, SHIELD_STANDARD
        self._init_equipment(
            capacitor_max=p["capacitor_max"], rate_max=p["generator_rate_max"],
            fuel_max=p["fuel_max"],
            shield_max_defense=ss["max_defense_energy"],
            shield_recovery_rate=ss["recovery_rate"],
            shield_recovery_cost=ss["recovery_energy_cost"],
            shield_deploy_cost=ss["deploy_energy_cost"],
            radar_range=p["radar_range"],
            missile_capacity=p["missile_capacity"],
            missile_power=ms["power"], missile_speed=ms["speed"],
            missile_flight_time=ms["flight_time"],
            missile_reload_time=MISSILE_RELOAD_TIME,
            beam_power=bs["power"], beam_speed=bs["speed"], beam_range=bs["range"],
        )
        self._attach_bot_crew()

    def _attach_bot_crew(self) -> None:
        from game.crew.navigator import Navigator
        from game.crew.gunner import Gunner
        from game.crew.bot_commander import BotCommander
        nav = Navigator(self)
        gun = Gunner(self)
        cmd = BotCommander(self)
        self.bridge.navigator = nav
        self.bridge.gunner = gun
        self.bridge.commander = cmd
