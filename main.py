"""Startreck エントリポイント。"""
import sys
import pygame
from game.universe import Universe
from game.coords import Vec2
from game.objects.vessel import Vessel
from game.objects.missile import Missile
from game.objects.beam import Beam
from game.objects.star import Star
from game.objects.base_station import BaseStation

SCREEN_W = 1200
SCREEN_H = 800
FPS = 60
BG_COLOR = (10, 10, 20)


def _color_for(obj) -> tuple:
    if isinstance(obj, Star):
        return (220, 220, 60)
    if isinstance(obj, BaseStation):
        return (255, 140, 0)
    if isinstance(obj, Vessel):
        return (100, 160, 255) if obj.faction == "U" else (255, 80, 80)
    if isinstance(obj, Missile):
        return (100, 255, 100) if obj.iff == "U" else (255, 120, 40)
    if isinstance(obj, Beam):
        return (80, 220, 255) if obj.iff == "U" else (255, 60, 60)
    return (160, 160, 160)


def _radius_for(obj) -> int:
    if isinstance(obj, Star):
        return max(3, int(obj.size * 0.6))
    if isinstance(obj, BaseStation):
        return 6
    if isinstance(obj, Vessel):
        return 5
    if isinstance(obj, (Missile, Beam)):
        return 3
    return 3


def draw_debug(screen: pygame.Surface, universe: Universe) -> None:
    for obj in universe.objects:
        sx = int(obj.pos.x / 10.0 * SCREEN_W)
        sy = int(obj.pos.y / 10.0 * SCREEN_H)
        pygame.draw.circle(screen, _color_for(obj), (sx, sy), _radius_for(obj))
        # 移動体に速度矢印
        if isinstance(obj, Vessel) and obj.speed > 0:
            ex = int(sx + obj.heading.x * 15)
            ey = int(sy + obj.heading.y * 15)
            pygame.draw.line(screen, _color_for(obj), (sx, sy), (ex, ey), 2)


def draw_hud(screen: pygame.Surface, font: pygame.font.Font,
             universe: Universe, vessels: list) -> None:
    lines = [f"Time: {universe.time}s   Objects: {len(universe.objects)}"]
    for v in vessels:
        if not v.destroyed:
            hp = f"{v.durability - v.damage:.0f}/{v.durability:.0f}gj"
            cap = f"{v.generator.capacitor:.0f}gj" if v.generator else "-"
            lines.append(
                f"[{v.faction}] HP:{hp}  Cap:{cap}  "
                f"Speed:{v.speed:.1f}  Pos:({v.pos.x:.2f},{v.pos.y:.2f})"
            )
    for i, line in enumerate(lines):
        surf = font.render(line, True, (200, 200, 200))
        screen.blit(surf, (10, 10 + i * 20))


def build_test_universe() -> tuple[Universe, list]:
    """Phase 3 動作確認用: 連邦とクリンゴンの駆逐艦を対峙させる。"""
    from game.vessels.destroyer import Destroyer
    uni = Universe()

    fed = Destroyer(Vec2(2.0, 5.0), faction="U")
    kli = Destroyer(Vec2(8.0, 5.0), faction="K")
    uni.add(fed)
    uni.add(kli)

    # 互いを認識させるため初回レーダースキャンを通知
    # (universe.time=0 の時点ではまだ update が走っていないため手動で実施)

    return uni, [fed, kli]


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Startreck")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    universe, vessels = build_test_universe()

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
        draw_debug(screen, universe)
        draw_hud(screen, font, universe, vessels)
        pygame.display.flip()

        winner = universe.victory
        if winner is not None:
            print(f"ゲーム終了: {'連邦' if winner == 'U' else 'クリンゴン'}の勝利")
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
