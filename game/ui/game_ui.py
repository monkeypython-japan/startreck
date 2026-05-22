"""GameUI: 全天マップ・レーダー・ステータス・メッセージ・ポップアップを統合管理。"""
from __future__ import annotations
import pygame
from game.ui.galaxy_map import GalaxyMap
from game.ui.radar_view import RadarView
from game.ui.message_window import MessageWindow
from game.ui.status_panel import StatusPanel
from game.ui.popup_menu import PopupMenu, MenuItem
from game.ui.font_util import make_font
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.universe import Universe
    from game.vessels.special_ship import SpecialShip
    from game.objects.thing import Thing

# ウィンドウ・レイアウト定数
WINDOW_W = 1440
WINDOW_H = 960
MAP_SIZE = 960          # 全天マップ: 正方形、ウィンドウ全高
PANEL_X = MAP_SIZE + 10 # 右パネル開始 X 座標
PANEL_W = WINDOW_W - PANEL_X  # 右パネル幅 (= 470)
RADAR_SIZE = PANEL_W    # レーダービュー: 正方形
STATUS_Y = RADAR_SIZE + 10
STATUS_H = 210
MSG_Y = STATUS_Y + STATUS_H + 8
MSG_H = WINDOW_H - MSG_Y - 4

BG_COLOR = (6, 6, 14)


class GameUI:
    def __init__(
        self,
        screen: pygame.Surface,
        universe: "Universe",
        player: "SpecialShip",
    ) -> None:
        self.screen = screen
        self.universe = universe
        self.player = player

        font = make_font(15)

        self.galaxy_map = GalaxyMap(
            pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE),
            player,
        )
        self.radar_view = RadarView(
            pygame.Rect(PANEL_X, 0, RADAR_SIZE, RADAR_SIZE),
            player,
        )
        self.status_panel = StatusPanel(
            pygame.Rect(PANEL_X, STATUS_Y, PANEL_W, STATUS_H),
            font,
        )
        self.message_window = MessageWindow(
            pygame.Rect(PANEL_X, MSG_Y, PANEL_W, MSG_H),
            font,
        )
        self.popup = PopupMenu(font, WINDOW_W, WINDOW_H)

        self._pending: str | None = None  # "jump_select"

        self.message_window.add("U.S.S. YUKIKAZE 出撃準備完了")
        self.message_window.add("マップをクリックして操作してください")

    # ─── イベント処理 ────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.popup.handle_mouse_motion(*event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_left_click(*event.pos)

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if pygame.Rect(PANEL_X, MSG_Y, PANEL_W, MSG_H).collidepoint(mx, my):
                self.message_window.scroll(-event.y * 20)

        elif event.type == pygame.KEYDOWN:
            self._handle_key(event.key)

    def _handle_left_click(self, mx: int, my: int) -> None:
        # ポップアップ優先
        if self.popup.visible:
            self.popup.handle_click(mx, my)
            return

        # クリックされたビューを特定
        in_galaxy = self.galaxy_map.contains(mx, my)
        in_radar = self.radar_view.contains(mx, my)
        if not in_galaxy and not in_radar:
            return

        # ジャンプ先選択モード
        if self._pending == "jump_select":
            view = self.galaxy_map if in_galaxy else self.radar_view
            objects = self.universe.objects
            clicked = (
                view.find_object_at(mx, my, objects)
                if in_galaxy
                else self.radar_view.find_object_at(mx, my)
            )
            from game.objects.base_station import BaseStation
            if clicked and isinstance(clicked, BaseStation) and clicked.faction == "U":
                self._cmd_jump(clicked)
            else:
                self.message_window.add("※ 連邦基地をクリックしてください")
            self._pending = None
            return

        # 通常クリック: オブジェクト選択またはエリア移動
        if in_galaxy:
            clicked = self.galaxy_map.find_object_at(mx, my, self.universe.objects)
            if clicked:
                self.galaxy_map.selected = clicked
                self.radar_view.selected = clicked
                self._show_object_menu(clicked, mx, my)
            else:
                world_pos = self.galaxy_map.screen_to_world(mx, my)
                self._show_move_speed_menu(world_pos, mx, my)
        else:
            clicked = self.radar_view.find_object_at(mx, my)
            if clicked:
                self.galaxy_map.selected = clicked
                self.radar_view.selected = clicked
                self._show_object_menu(clicked, mx, my)
            else:
                world_pos = self.radar_view.screen_to_world(mx, my)
                self._show_move_speed_menu(world_pos, mx, my)

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_SPACE:
            self._cmd_stop()
        elif key == pygame.K_s:
            rate = 0 if (self.player.shield and self.player.shield.set_rate > 0) else 100
            self._cmd_shield(rate)

    # ─── ポップアップメニュー構築 ─────────────────────────────

    def _show_object_menu(self, obj: "Thing", mx: int, my: int) -> None:
        from game.objects.vessel import Vessel
        from game.objects.base_station import BaseStation
        from game.vessels.special_ship import SpecialShip

        items: list[MenuItem] = []

        if isinstance(obj, SpecialShip) and obj is self.player:
            items = [
                MenuItem("停止 [SPACE]", self._cmd_stop),
                MenuItem("シールド 0%", lambda: self._cmd_shield(0)),
                MenuItem("シールド 50%", lambda: self._cmd_shield(50)),
                MenuItem("シールド 100%", lambda: self._cmd_shield(100)),
            ]
            if self.player.jump_drive:
                ready = (self.player.generator is not None and
                         self.player.generator.capacitor >= self.player.jump_drive.required_energy)
                items.append(MenuItem("ジャンプ先を選択", self._start_jump_select, ready))

        elif isinstance(obj, Vessel) and obj.faction != self.player.faction:
            has_missile = bool(self.player.missile_launcher and self.player.missile_launcher.stock > 0)
            items = [
                MenuItem("ミサイル攻撃", lambda o=obj: self._cmd_missile(o), has_missile),
                MenuItem("ビーム攻撃", lambda o=obj: self._cmd_beam(o)),
                MenuItem("この目標へ移動", lambda o=obj: self._show_move_speed_menu(o.pos, mx, my)),
            ]

        elif isinstance(obj, BaseStation) and obj.faction == "U":
            ready = (self.player.jump_drive is not None and
                     self.player.generator is not None and
                     self.player.generator.capacitor >= self.player.jump_drive.required_energy)
            items = [
                MenuItem("この基地へ移動", lambda o=obj: self._show_move_speed_menu(o.pos, mx, my)),
                MenuItem("ジャンプ", lambda o=obj: self._cmd_jump(o), ready),
            ]

        elif isinstance(obj, Vessel) and obj.faction == self.player.faction:
            items = [
                MenuItem("この艦へ移動", lambda o=obj: self._show_move_speed_menu(o.pos, mx, my)),
            ]

        if items:
            self.popup.show(mx, my, items)

    def _show_move_speed_menu(self, target_pos, mx: int, my: int) -> None:
        ms = self.player.max_speed
        items = [
            MenuItem(f"最大速度  ({ms:.0f} g/s) で移動",
                     lambda p=target_pos: self._cmd_move_to(p, ms)),
            MenuItem(f"半速      ({ms/2:.0f} g/s) で移動",
                     lambda p=target_pos: self._cmd_move_to(p, ms / 2)),
            MenuItem(f"低速      ({ms/4:.0f} g/s) で移動",
                     lambda p=target_pos: self._cmd_move_to(p, ms / 4)),
            MenuItem("停止", self._cmd_stop),
        ]
        self.popup.show(mx, my, items)

    def _start_jump_select(self) -> None:
        self._pending = "jump_select"
        self.message_window.add("ジャンプ先の連邦基地をクリックしてください")

    # ─── コマンド ─────────────────────────────────────────────

    def _cmd_move_to(self, pos, speed: float) -> None:
        nav = self.player.bridge and self.player.bridge.navigator
        if nav:
            nav.set_destination(pos, speed)
            self.message_window.add(f"移動: ({pos.x:.1f}, {pos.y:.1f})  速度 {speed:.0f} g/s")

    def _cmd_stop(self) -> None:
        nav = self.player.bridge and self.player.bridge.navigator
        if nav:
            nav.stop()
            self.message_window.add("停止命令")

    def _cmd_missile(self, target: "Thing") -> None:
        gun = self.player.bridge and self.player.bridge.gunner
        if gun:
            gun.attack_missile(target)
            self.message_window.add("ミサイル発射指示")

    def _cmd_beam(self, target: "Thing") -> None:
        gun = self.player.bridge and self.player.bridge.gunner
        if gun:
            gun.attack_beam(target)
            self.message_window.add("ビーム発射指示")

    def _cmd_shield(self, rate: float) -> None:
        if self.player.shield:
            self.player.shield.set_defense_rate(rate)
            self.message_window.add(f"シールド設定: {rate:.0f}%")

    def _cmd_jump(self, base) -> None:
        if self.player.jump_drive and self.player.generator:
            ok = self.player.jump_drive.jump(base, self.player.generator)
            self.message_window.add("ジャンプ実行!" if ok else "ジャンプ失敗: エネルギー不足")

    # ─── 描画 ──────────────────────────────────────────────────

    def _collect_messages(self) -> None:
        while self.player.messages:
            self.message_window.add(self.player.messages.pop(0))

    def draw(self) -> None:
        self._collect_messages()
        self.screen.fill(BG_COLOR)
        self.galaxy_map.draw(self.screen, self.universe)
        self.radar_view.draw(self.screen)
        self.status_panel.draw(self.screen, self.universe, self.player)
        self.message_window.draw(self.screen)
        self.popup.draw(self.screen)
