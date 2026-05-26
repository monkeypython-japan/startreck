"""護衛型巡洋艦: 重巡洋艦のコマンダーを BotGuardCommander に設定したもの。"""
from __future__ import annotations
from game.coords import Vec2
from game.vessels.heavy_cruiser import HeavyCruiser


class GuardCruiser(HeavyCruiser):
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
