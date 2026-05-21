"""Startreck エントリポイント。"""
import sys
import pygame
from game.universe import Universe

SCREEN_W = 1200
SCREEN_H = 800
FPS = 60
BG_COLOR = (10, 10, 20)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Startreck")
    clock = pygame.time.Clock()

    universe = Universe()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # 秒

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        universe.update(dt)

        screen.fill(BG_COLOR)
        pygame.display.flip()

        winner = universe.victory
        if winner is not None:
            print(f"ゲーム終了: {'連邦' if winner == 'U' else 'クリンゴン'}の勝利")
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
