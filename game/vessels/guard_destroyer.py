"""護衛型駆逐艦: 駆逐艦のコマンダーを BotGuardCommander に設定したもの。"""
from __future__ import annotations
from game.coords import Vec2
from game.vessels.destroyer import Destroyer


class GuardDestroyer(Destroyer):
    def __init__(self, pos: Vec2, faction: str) -> None:
        super().__init__(pos, faction)
        from game import names
        self.name = names.next_fed_vessel_name() if faction == "U" else names.next_kli_guard_name()

    def _attach_bot_crew(self) -> None:
        from game.crew.navigator import Navigator
        from game.crew.gunner import Gunner
        from game.crew.bot_guard_commander import BotGuardCommander
        nav = Navigator(self)
        gun = Gunner(self)
        cmd = BotGuardCommander(self)
        self.bridge.navigator = nav
        self.bridge.gunner = gun
        self.bridge.commander = cmd
