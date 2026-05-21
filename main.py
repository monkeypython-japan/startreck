"""Startreck エントリポイント。"""
import sys
import pygame
from game.universe import Universe
from game.initializer import initialize
from game.objects.vessel import Vessel
from game.objects.missile import Missile
from game.objects.beam import Beam
from game.objects.star import Star
from game.objects.base_station import BaseStation
from game.vessels.special_ship import SpecialShip

SCREEN_W = 1200
SCREEN_H = 800
FPS = 60
BG_COLOR = (10, 10, 20)
GRID_COLOR = (30, 35, 50)


def _color_for(obj) -> tuple:
    if isinstance(obj, Star):
        return (220, 220, 60)
    if isinstance(obj, BaseStation):
        return (255, 140, 0)
    if isinstance(obj, SpecialShip):
        return (255, 255, 100)
    if isinstance(obj, Vessel):
        return (100, 160, 255) if obj.faction == "U" else (255, 80, 80)
    if isinstance(obj, Missile):
        return (100, 255, 100) if obj.iff == "U" else (255, 120, 40)
    if isinstance(obj, Beam):
        return (80, 220, 255) if obj.iff == "U" else (255, 60, 60)
    return (160, 160, 160)


def _radius_for(obj) -> int:
    if isinstance(obj, Star):
        return max(3, int(obj.size * 0.8))
    if isinstance(obj, BaseStation):
        return 7
    if isinstance(obj, SpecialShip):
        return 6
    if isinstance(obj, Vessel):
        return 4
    if isinstance(obj, (Missile, Beam)):
        return 2
    return 3


def world_to_screen(pos, w: int, h: int) -> tuple[int, int]:
    return int(pos.x / 10.0 * w), int(pos.y / 10.0 * h)


def draw_grid(screen: pygame.Surface) -> None:
    """セクタ境界を薄い線で描画。"""
    w, h = screen.get_size()
    for i in range(1, 10):
        x = int(i / 10 * w)
        y = int(i / 10 * h)
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, h))
        pygame.draw.line(screen, GRID_COLOR, (0, y), (w, y))


def draw_objects(screen: pygame.Surface, universe: Universe) -> None:
    w, h = screen.get_size()
    for obj in universe.objects:
        sx, sy = world_to_screen(obj.pos, w, h)
        color = _color_for(obj)
        r = _radius_for(obj)
        pygame.draw.circle(screen, color, (sx, sy), r)
        # 移動体に速度矢印
        if isinstance(obj, Vessel) and obj.speed > 0:
            ex = int(sx + obj.heading.x * 14)
            ey = int(sy + obj.heading.y * 14)
            pygame.draw.line(screen, color, (sx, sy), (ex, ey), 2)
        # ビームは origin〜tip の線
        if isinstance(obj, Beam):
            ox, oy = world_to_screen(obj.origin, w, h)
            pygame.draw.line(screen, color, (ox, oy), (sx, sy), 1)


def draw_hud(screen: pygame.Surface, font: pygame.font.Font,
             universe: Universe, player: SpecialShip) -> None:
    w = screen.get_width()
    lines = [f"Time: {universe.time}s   Objects: {len(universe.objects)}"]
    if not player.destroyed:
        hp = f"{player.durability - player.damage:.0f}/{player.durability:.0f}gj"
        cap = f"{player.generator.capacitor:.0f}/{player.generator.capacitor_max:.0f}gj" \
              if player.generator else "-"
        fuel = f"{player.generator.fuel:.0f}gj" if player.generator else "-"
        missiles = player.missile_launcher.stock if player.missile_launcher else 0
        shield = f"{player.shield.current_rate:.0f}%" if player.shield else "-"
        sx, sy = int(player.pos.x * 100) // 100, int(player.pos.y * 100) // 100
        sec = f"{int(player.pos.x)}-{int(player.pos.y)}"
        lines += [
            f"U.S.S. YUKIKAZE  Sector:{sec}  HP:{hp}",
            f"Capacitor:{cap}  Fuel:{fuel}  Missiles:{missiles}  Shield:{shield}",
            f"Speed:{player.speed:.1f} grid/s",
        ]
    else:
        lines.append("U.S.S. YUKIKAZE DESTROYED")

    fed_bases = sum(1 for o in universe.objects
                    if isinstance(o, BaseStation) and o.faction == "U")
    klingons = sum(1 for o in universe.objects
                   if isinstance(o, Vessel) and o.faction == "K")
    lines.append(f"Federation Bases: {fed_bases}   Klingons: {klingons}")

    for i, line in enumerate(lines):
        surf = font.render(line, True, (200, 200, 200))
        screen.blit(surf, (10, 10 + i * 20))

    # 操作説明
    hint = "ESC: Quit"
    screen.blit(font.render(hint, True, (100, 100, 100)), (w - 120, 10))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Startreck")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    universe = Universe()
    player = initialize(universe)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        universe.update(dt)

        screen.fill(BG_COLOR)
        draw_grid(screen)
        draw_objects(screen, universe)
        draw_hud(screen, font, universe, player)
        pygame.display.flip()

        winner = universe.victory
        if winner is not None:
            msg = "連邦の勝利！" if winner == "U" else "クリンゴンの勝利！"
            print(f"ゲーム終了: {msg}  (Time: {universe.time}s)")
            # 結果を3秒間表示してから終了
            result_surf = pygame.font.SysFont("monospace", 48).render(msg, True, (255, 255, 100))
            screen.blit(result_surf, (SCREEN_W // 2 - result_surf.get_width() // 2,
                                      SCREEN_H // 2 - 24))
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
