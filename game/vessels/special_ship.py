"""特務艦 U.S.S. YUKIKAZE: プレーヤー機。ジャンプドライブ搭載。"""
from __future__ import annotations
from game.coords import Vec2
from game.objects.vessel import Vessel
from game.constants import SPECIAL_SHIP, MISSILE_SPECIAL, BEAM_SPECIAL, SHIELD_SPECIAL


class SpecialShip(Vessel):
    def __init__(self, pos: Vec2) -> None:
        p = SPECIAL_SHIP
        super().__init__(
            pos=pos, size=p["size"], durability=p["durability"],
            max_speed=p["max_speed"], faction="U",
            supply_provider=p["supply_provider"],
        )
        ms, bs, ss = MISSILE_SPECIAL, BEAM_SPECIAL, SHIELD_SPECIAL
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
            beam_power=bs["power"], beam_speed=bs["speed"], beam_range=bs["range"],
        )
        # ジャンプドライブ装備
        from game.equipment.jump_drive import JumpDrive
        self.jump_drive = JumpDrive(self, p["capacitor_max"], on_report=self._report)

        # Phase 3 テスト用: BOT クルー。Phase 5 で Player に交替
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

    def attach_player(self) -> None:
        """Phase 5 でプレーヤーに切り替える。"""
        from game.crew.navigator import Navigator
        from game.crew.gunner import Gunner
        from game.crew.player import Player
        self.bridge.navigator = Navigator(self)
        self.bridge.gunner = Gunner(self)
        self.bridge.commander = Player(self)
