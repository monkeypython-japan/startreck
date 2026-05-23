"""Startreck エントリポイント。"""
import sys
import pygame
from game.universe import Universe
from game.initializer import initialize
from game.ui.game_ui import GameUI, WINDOW_W, WINDOW_H
from game.ui.font_util import make_font

FPS = 60


def _run_game(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """1ゲームセッションを実行し、終了理由 ("reset" | "quit") を返す。"""
    universe = Universe()
    player = initialize(universe)
    ui = GameUI(screen, universe, player)
    font_large = make_font(56)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"
            else:
                ui.handle_event(event)

        if ui.quit_requested:
            return "quit"
        if ui.reset_requested:
            return "reset"

        if not ui.is_paused:
            universe.update(dt)

        ui.draw()
        pygame.display.flip()

        if not ui.is_paused:
            winner = universe.victory
            if winner is not None:
                msg = "連邦の勝利！" if winner == "U" else "クリンゴンの勝利！"
                print(f"ゲーム終了: {msg}  (Time: {universe.time}s)")
                result_surf = font_large.render(msg, True, (255, 255, 100))
                screen.blit(result_surf, (WINDOW_W // 2 - result_surf.get_width() // 2,
                                          WINDOW_H // 2 - 24))
                pygame.display.flip()
                pygame.time.wait(3000)
                return "quit"


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Startreck")
    clock = pygame.time.Clock()

    result = "reset"
    while result == "reset":
        result = _run_game(screen, clock)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
