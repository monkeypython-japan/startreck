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
BTN_H = 32              # コントロールバーボタン高さ
BTN_PAD = 4
CTRL_Y = WINDOW_H - BTN_H - BTN_PAD  # コントロールバー Y 座標
MSG_H = CTRL_Y - BTN_PAD - MSG_Y     # メッセージウィンド高さ

BG_COLOR = (6, 6, 14)
BTN_BORDER = (100, 120, 160)
BTN_TEXT   = (210, 225, 240)


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
        self._explosions: list[dict] = []  # 爆発エフェクトリスト

        # コントロールバー
        self._game_state: str = "ready"  # "ready" | "running" | "paused"
        self.reset_requested: bool = False
        self.quit_requested: bool = False
        self._btn_font = make_font(13)
        bw = (PANEL_W - BTN_PAD * 4) // 3
        bw_last = PANEL_W - BTN_PAD * 4 - bw * 2
        self._btn_start = pygame.Rect(PANEL_X + BTN_PAD, CTRL_Y, bw, BTN_H)
        self._btn_reset = pygame.Rect(PANEL_X + BTN_PAD * 2 + bw, CTRL_Y, bw, BTN_H)
        self._btn_quit  = pygame.Rect(PANEL_X + BTN_PAD * 3 + bw * 2, CTRL_Y, bw_last, BTN_H)

        self.message_window.add("U.S.S. YUKIKAZE 出撃準備完了")
        self.message_window.add("▶ スタート ボタンを押してゲーム開始")

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

    @property
    def is_paused(self) -> bool:
        return self._game_state != "running"

    def _handle_left_click(self, mx: int, my: int) -> None:
        # コントロールバーボタン
        if self._btn_start.collidepoint(mx, my):
            self._on_btn_start()
            return
        if self._btn_reset.collidepoint(mx, my):
            self.reset_requested = True
            return
        if self._btn_quit.collidepoint(mx, my):
            self.quit_requested = True
            return

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

    def _on_btn_start(self) -> None:
        if self._game_state == "ready":
            self._game_state = "running"
            self.message_window.add("ゲーム開始")
        elif self._game_state == "running":
            self._game_state = "paused"
            self.message_window.add("一時停止")
        else:
            self._game_state = "running"
            self.message_window.add("再開")

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_SPACE:
            self._cmd_stop()
        elif key == pygame.K_s:
            gun = self.player.bridge and self.player.bridge.gunner
            current = gun._manual_shield_rate if gun else 0
            rate = 0 if current > 0 else 100
            self._cmd_shield(rate)

    # ─── ポップアップメニュー構築 ─────────────────────────────

    def _show_object_menu(self, obj: "Thing", mx: int, my: int) -> None:
        from game.objects.vessel import Vessel
        from game.objects.base_station import BaseStation
        from game.vessels.special_ship import SpecialShip

        items: list[MenuItem] = []

        if isinstance(obj, SpecialShip) and obj is self.player:
            from game.coords import distance_grid
            from game.constants import SUPPLY_RANGE
            from game.objects.base_station import BaseStation as BS
            can_supply = any(
                isinstance(o, BS) and o.faction == "U"
                and distance_grid(self.player.pos, o.pos) <= SUPPLY_RANGE
                for o in self.universe.objects
            )
            items = [
                MenuItem("停止 [SPACE]", self._cmd_stop),
                MenuItem("シールド 0%", lambda: self._cmd_shield(0)),
                MenuItem("シールド 50%", lambda: self._cmd_shield(50)),
                MenuItem("シールド 100%", lambda: self._cmd_shield(100)),
            ]
            if can_supply:
                items.append(MenuItem("補給", self._cmd_supply))
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
        gun = self.player.bridge and self.player.bridge.gunner
        if gun:
            gun.set_manual_shield_rate(rate)
            self.message_window.add(f"シールド設定: {rate:.0f}%")

    def _cmd_supply(self) -> None:
        self.player.supply_full()
        self.message_window.add("補給完了: ダメージ回復・燃料・ミサイル満載")

    def _cmd_jump(self, base) -> None:
        if self.player.jump_drive and self.player.generator:
            ok = self.player.jump_drive.jump(base, self.player.generator)
            self.message_window.add("ジャンプ実行!" if ok else "ジャンプ失敗: エネルギー不足")

    # ─── 描画 ──────────────────────────────────────────────────

    def _collect_messages(self) -> None:
        from game.constants import REPORT_ALERT
        while self.player.messages:
            msg = self.player.messages.pop(0)
            if msg.startswith(REPORT_ALERT):
                self.message_window.add_alert(msg[len(REPORT_ALERT):])
            else:
                self.message_window.add(msg)

    def _collect_explosions(self) -> None:
        import pygame
        now_ms = pygame.time.get_ticks()
        for pos in self.universe.recent_explosions:
            self._explosions.append({"pos": pos, "start_ms": now_ms, "duration": 1.5, "max_r": 20})
        self.universe.recent_explosions.clear()
        self._explosions = [e for e in self._explosions
                            if (now_ms - e["start_ms"]) / 1000.0 < e["duration"]]

    def _draw_button(self, rect: pygame.Rect, label: str, bg: tuple) -> None:
        pygame.draw.rect(self.screen, bg, rect, border_radius=4)
        pygame.draw.rect(self.screen, BTN_BORDER, rect, 1, border_radius=4)
        txt = self._btn_font.render(label, True, BTN_TEXT)
        self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))

    def _draw_controls(self) -> None:
        if self._game_state == "ready":
            start_label, start_bg = "▶ スタート", (30, 100, 50)
        elif self._game_state == "running":
            start_label, start_bg = "一時停止", (110, 90, 20)
        else:
            start_label, start_bg = "▶ 再開", (20, 80, 140)
        self._draw_button(self._btn_start, start_label, start_bg)
        self._draw_button(self._btn_reset, "リセット", (50, 55, 85))
        self._draw_button(self._btn_quit,  "終了",     (90, 25, 25))

    def draw(self) -> None:
        self._collect_messages()
        self._collect_explosions()
        self.screen.fill(BG_COLOR)
        self.galaxy_map.draw(self.screen, self.universe)
        self.galaxy_map.draw_explosions(self.screen, self._explosions)
        self.radar_view.draw(self.screen)
        self.radar_view.draw_explosions(self.screen, self._explosions)
        self.status_panel.draw(self.screen, self.universe, self.player)
        self.message_window.draw(self.screen)
        self._draw_controls()
        self.popup.draw(self.screen)
