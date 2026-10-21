"""Небольшой дымовой тест: создаёт окно, играет несколько кадров, закрывает.

Запуск:  python smoke_test.py
"""

import tkinter as tk

from snake import DOWN, SnakeApp, SnakeGame


def main() -> None:
    root = tk.Tk()
    app = SnakeApp(root, SnakeGame(cols=12, rows=12))

    # Прогоняем несколько кадров игрового цикла вручную.
    for _ in range(5):
        app._tick()
        root.update()

    assert len(app.game.snake) == 3, app.game.snake
    assert app.game.food is not None
    assert not app.game.over

    # Поворот и пауза
    app.game.set_direction(DOWN)
    app._tick()
    root.update()
    assert app.game.direction == DOWN

    app.game.toggle_pause()
    app._draw()
    root.update()
    assert app.game.paused

    # Экран «игра окончена» рисуется без ошибок
    app.game.over = True
    app.game.death_reason = "Тест"
    app._draw()
    root.update()

    app.close()
    print("SMOKE OK: окно создано, кадры отрисованы, закрытие без ошибок")


if __name__ == "__main__":
    main()
