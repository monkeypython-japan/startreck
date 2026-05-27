"""宇宙: ゲームのメインループとオブジェクト管理。"""
from __future__ import annotations
from game.objects.thing import Thing


class Universe:
    def __init__(self) -> None:
        self.objects: list[Thing] = []
        self.time: int = 0
        self._elapsed: float = 0.0
        self._initialized: bool = False  # initialize() が呼ばれた後に True
        self.recent_explosions: list = []  # UIが毎フレーム読み取り後にクリアする
        self.destroyed_bases: list[tuple] = []  # (pos, faction) 破壊済み基地の永続記録
        self._destroyed_vessel_stats: list[dict] = []  # ログ用: 破壊済み艦艇の統計スナップショット

    def add(self, obj: Thing) -> None:
        self.objects.append(obj)
        from game.objects.vessel import Vessel
        if isinstance(obj, Vessel):
            obj.universe = self

    def remove_destroyed(self) -> None:
        from game.objects.missile import Missile
        from game.objects.beam import Beam
        from game.objects.base_station import BaseStation
        from game.objects.vessel import Vessel
        for o in self.objects:
            if o.destroyed and not isinstance(o, (Missile, Beam)):
                self.recent_explosions.append(o.pos)
                if isinstance(o, BaseStation):
                    self.destroyed_bases.append((o.pos, o.faction))
                elif isinstance(o, Vessel):
                    self._destroyed_vessel_stats.append({
                        "faction": o.faction,
                        "ml_capacity": o.missile_launcher.capacity if o.missile_launcher else 0,
                        "ml_fired": o.missile_launcher.shots_fired if o.missile_launcher else 0,
                        "ml_stock": o.missile_launcher.stock if o.missile_launcher else 0,
                        "fuel_max": o.generator.fuel_max if o.generator else 0.0,
                        "fuel_consumed": o.generator.fuel_consumed if o.generator else 0.0,
                        "fuel_remaining": o.generator.fuel if o.generator else 0.0,
                    })
        self.objects = [o for o in self.objects if not o.destroyed]

    def update(self, dt: float) -> None:
        self.remove_destroyed()
        for obj in list(self.objects):
            obj.update(dt)
        self._check_weapon_collisions()
        self._elapsed += dt
        while self._elapsed >= 1.0:
            self._elapsed -= 1.0
            self.time += 1
            self._tick()

    def _check_weapon_collisions(self) -> None:
        from game.objects.missile import Missile
        from game.objects.beam import Beam
        non_weapons = [o for o in self.objects if not isinstance(o, (Missile, Beam))]
        for obj in list(self.objects):
            if isinstance(obj, Missile):
                obj.check_detonation(non_weapons)
            elif isinstance(obj, Beam):
                obj.check_damage(non_weapons)

    def _tick(self) -> None:
        from game.objects.vessel import Vessel
        self._sync_fleet_integrators()
        for obj in list(self.objects):
            if isinstance(obj, Vessel) and obj.bridge and obj.bridge.commander:
                obj.bridge.commander.tick()

    def _sync_fleet_integrators(self) -> None:
        """フリートインテグレータ同期: 僚艦データの共有と破壊済みレコードの除去。"""
        from game.objects.vessel import Vessel
        from game.objects.base_station import BaseStation
        from game.objects.star import Star
        active_ids = {obj.id for obj in self.objects}
        stars = [o for o in self.objects if isinstance(o, Star)]

        # 各勢力ごとに、いずれかの味方レーダーが捉えた敵の接触情報を収集
        faction_enemy_contacts: dict[str, dict[str, "Thing"]] = {}
        for obj in self.objects:
            if isinstance(obj, Vessel) and obj.radar:
                f = obj.faction
                if f not in faction_enemy_contacts:
                    faction_enemy_contacts[f] = {}
                for contact in obj.radar.contacts:
                    if getattr(contact, "faction", "") != f:
                        faction_enemy_contacts[f][contact.id] = contact
        # 基地レーダースキャン: 探知した敵を勢力共有インテルに追加
        for obj in self.objects:
            if isinstance(obj, BaseStation):
                obj.radar.scan(self.objects, self.time)
                f = obj.faction
                if f not in faction_enemy_contacts:
                    faction_enemy_contacts[f] = {}
                for contact in obj.radar.contacts:
                    if getattr(contact, "faction", "") != f:
                        faction_enemy_contacts[f][contact.id] = contact

        # 敵基地の新規発見を検出するため、各勢力の既知敵基地IDを事前収集
        known_enemy_base_ids: dict[str, set[str]] = {}
        for obj in self.objects:
            if isinstance(obj, Vessel) and obj.integrator:
                f = obj.faction
                if f not in known_enemy_base_ids:
                    enemy_f = "K" if f == "U" else "U"
                    known_enemy_base_ids[f] = {
                        r.id for r in obj.integrator.query(faction=enemy_f)
                        if r.obj_type == "BaseStation"
                    }
                    break  # 同勢力の1艦分で代表

        for obj in self.objects:
            if not isinstance(obj, Vessel) or not obj.integrator:
                continue
            obj.integrator.remove_destroyed(active_ids)
            f = obj.faction
            # 恒星は双方に既知 — 常時反映
            for star in stars:
                obj.integrator.record(star, self.time)
            # 同勢力オブジェクトを常時反映
            for ally in self.objects:
                if getattr(ally, "faction", "") == f and ally is not obj:
                    obj.integrator.record(ally, self.time)
            # 味方レーダーで捕捉した敵を共有
            for contact in faction_enemy_contacts.get(f, {}).values():
                obj.integrator.record(contact, self.time)

        # 敵基地が新規登録された勢力はフリートコマンダーの目標を即時更新
        from game.crew.bot_fleet_commander import BotFleetCommander
        updated_factions: set[str] = set()
        for obj in self.objects:
            if isinstance(obj, Vessel) and obj.integrator:
                f = obj.faction
                if f in updated_factions:
                    continue
                enemy_f = "K" if f == "U" else "U"
                new_ids = {
                    r.id for r in obj.integrator.query(faction=enemy_f)
                    if r.obj_type == "BaseStation"
                }
                if new_ids != known_enemy_base_ids.get(f, set()):
                    # 新規発見または消滅: この勢力のフリートコマンダー全員に即時通知
                    for vessel in self.objects:
                        if (isinstance(vessel, Vessel) and vessel.faction == f
                                and vessel.bridge
                                and isinstance(vessel.bridge.commander, BotFleetCommander)):
                            vessel.bridge.commander.update_fleet_target()
                    updated_factions.add(f)

    @property
    def victory(self) -> str | None:
        """勝者を返す。未初期化またはゲーム継続中は None。"""
        if not self._initialized:
            return None
        from game.objects.base_station import BaseStation

        bases_U = [o for o in self.objects
                   if isinstance(o, BaseStation) and o.faction == "U"]
        bases_K = [o for o in self.objects
                   if isinstance(o, BaseStation) and o.faction == "K"]
        if not bases_U:
            return "K"
        if not bases_K:
            return "U"
        return None
