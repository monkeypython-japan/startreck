"""インテグレータ: 艦艇ごとの全天マップ（レーダー探知記録）。"""
from __future__ import annotations
from dataclasses import dataclass
from game.coords import Vec2
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing


@dataclass
class ObjectRecord:
    id: str
    pos: Vec2
    faction: str   # "U", "K", ""
    obj_type: str  # クラス名
    last_seen: int  # ゲーム時刻 (秒)


class Integrator(Equipment):
    def __init__(self, owner: "Thing") -> None:
        super().__init__(owner)
        self.star_map: dict[str, ObjectRecord] = {}

    def record(self, obj: "Thing", game_time: int) -> None:
        """レーダー探知オブジェクトを全天マップに記録・更新する。"""
        faction = getattr(obj, "faction", "")
        self.star_map[obj.id] = ObjectRecord(
            id=obj.id,
            pos=obj.pos,
            faction=faction,
            obj_type=type(obj).__name__,
            last_seen=game_time,
        )

    def get(self, obj_id: str) -> ObjectRecord | None:
        return self.star_map.get(obj_id)

    def query(self, faction: str | None = None) -> list[ObjectRecord]:
        records = list(self.star_map.values())
        if faction is not None:
            records = [r for r in records if r.faction == faction]
        return records

    def remove_destroyed(self, active_ids: set[str]) -> None:
        """宇宙から削除されたオブジェクトの記録をクリアする。"""
        for oid in list(self.star_map.keys()):
            if oid not in active_ids:
                del self.star_map[oid]
