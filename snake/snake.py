"""Игра «Змейка» на Python.

Реализация на стандартной библиотеке (tkinter) — дополнительные
зависимости устанавливать не нужно.

Архитектура разделена на два слоя:
  * SnakeGame — чистая логика (сетка, змейка, еда, счёт, столкновения).
    Не зависит от tkinter, поэтому её легко покрыть тестами.
  * SnakeApp  — отрисовка, ввод с клавиатуры и игровой цикл.

Запуск:  python snake.py
"""

from __future__ import annotations

import random
import tkinter as tk
from typing import List, Optional, Tuple

# --------------------------------------------------------------------------
# Настройки игры
# --------------------------------------------------------------------------

COLS = 20                 # ширина поля в клетках
ROWS = 20                 # высота поля в клетках
CELL_SIZE = 24            # размер клетки в пикселях
START_LENGTH = 3          # начальная длина змейки
BASE_SPEED_MS = 140       # задержка между шагами в начале (меньше — быстрее)
SPEED_STEP_MS = 7         # ускорение за каждую съеденную еду
MIN_SPEED_MS = 55         # максимальная скорость
SCORE_PER_FOOD = 10

Cell = Tuple[int, int]

# Направления
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# Соответствие клавиш направлениям (ключи в нижнем регистре)
KEY_TO_DIRECTION = {
    "up": UP, "down": DOWN, "left": LEFT, "right": RIGHT,
    "w": UP, "s": DOWN, "a": LEFT, "d": RIGHT,
    "ц": UP, "ы": DOWN, "ф": LEFT, "в": RIGHT,
}


# --------------------------------------------------------------------------
# Игровая логика
# --------------------------------------------------------------------------

class SnakeGame:
    """Состояние и правила игры «Змейка» без какой-либо графики."""

    def __init__(
        self,
        cols: int = COLS,
        rows: int = ROWS,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.cols = cols
        self.rows = rows
        self.rng = rng or random.Random()
        self.snake: List[Cell] = []
        self.direction: Cell = RIGHT
        self.next_direction: Cell = RIGHT
        self.food: Optional[Cell] = None
        self.score = 0
        self.food_eaten = 0
        self.over = False
        self.won = False
        self.paused = False
        self.death_reason = ""
        self.reset()

    # -- служебное ---------------------------------------------------------

    def _all_cells(self) -> List[Cell]:
        return [(x, y) for x in range(self.cols) for y in range(self.rows)]

    @property
    def head(self) -> Cell:
        return self.snake[0]

    @property
    def speed_ms(self) -> int:
        """Задержка между шагами: чем больше съедено еды, тем быстрее игра."""
        return max(MIN_SPEED_MS, BASE_SPEED_MS - SPEED_STEP_MS * self.food_eaten)

    # -- жизненный цикл ----------------------------------------------------

    def reset(self) -> None:
        """Начинает игру заново."""
        head = (self.cols // 2, self.rows // 2)
        self.snake = [head] + [(head[0] - i, head[1]) for i in range(1, START_LENGTH)]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.food_eaten = 0
        self.over = False
        self.won = False
        self.paused = False
        self.death_reason = ""
        self.food = self._spawn_food()

    def _spawn_food(self) -> Optional[Cell]:
        """Ставит еду на случайную свободную клетку. None — поле заполнено."""
        occupied = set(self.snake)
        free = [cell for cell in self._all_cells() if cell not in occupied]
        if not free:
            return None
        return self.rng.choice(free)

    # -- управление --------------------------------------------------------

    def set_direction(self, direction: Cell) -> bool:
        """Меняет направление. Разворот на 180 градусов запрещён.

        Сравниваем с текущим направлением, а не с отложенным: иначе
        последовательность «вправо → вверх → влево» развернула бы змейку
        прямо в её собственное тело.
        """
        if direction not in DIRECTIONS:
            return False
        if self.over or self.won:
            return False
        if direction == OPPOSITE[self.direction]:
            return False
        self.next_direction = direction
        return True

    def toggle_pause(self) -> None:
        if not self.over and not self.won:
            self.paused = not self.paused

    # -- игровой шаг -------------------------------------------------------

    def step(self) -> None:
        """Сдвигает змейку на одну клетку."""
        if self.over or self.won or self.paused:
            return

        self.direction = self.next_direction
        dx, dy = self.direction
        hx, hy = self.head
        new_head = (hx + dx, hy + dy)

        # Столкновение со стеной
        if not (0 <= new_head[0] < self.cols and 0 <= new_head[1] < self.rows):
            self.over = True
            self.death_reason = "Столкновение со стеной"
            return

        growing = self.food is not None and new_head == self.food
        # Если змейка не растёт, хвост на этом шаге освобождает клетку.
        body = self.snake if growing else self.snake[:-1]
        if new_head in body:
            self.over = True
            self.death_reason = "Столкновение с самим собой"
            return

        self.snake.insert(0, new_head)

        if growing:
            self.score += SCORE_PER_FOOD
            self.food_eaten += 1
            self.food = self._spawn_food()
            if self.food is None:
                self.won = True
                self.death_reason = "Поле заполнено — победа!"
        else:
            self.snake.pop()


# --------------------------------------------------------------------------
# Отрисовка и игровой цикл
# --------------------------------------------------------------------------

class SnakeApp:
    """Окно игры: рисует поле, обрабатывает клавиши, крутит таймер."""

    COLORS = {
        "bg": "#0f172a",
        "grid": "#1e293b",
        "snake": "#22c55e",
        "head": "#a7f3d0",
        "food": "#ef4444",
        "text": "#e2e8f0",
        "hint": "#64748b",
        "overlay": "#0f172a",
    }

    def __init__(self, root: tk.Tk, game: Optional[SnakeGame] = None) -> None:
        self.root = root
        self.game = game or SnakeGame()
        self._timer: Optional[str] = None
        self._closed = False

        root.title("Змейка")
        root.resizable(False, False)
        root.configure(background=self.COLORS["bg"])
        root.protocol("WM_DELETE_WINDOW", self.close)

        header = tk.Frame(root, bg=self.COLORS["bg"])
        header.pack(pady=(10, 6))
        self.score_label = tk.Label(
            header, text="", bg=self.COLORS["bg"], fg=self.COLORS["text"],
            font=("Segoe UI", 13, "bold"),
        )
        self.score_label.pack()

        self.canvas = tk.Canvas(
            root,
            width=self.game.cols * CELL_SIZE,
            height=self.game.rows * CELL_SIZE,
            bg=self.COLORS["bg"],
            highlightthickness=0,
        )
        self.canvas.pack()

        tk.Label(
            root,
            text="Стрелки / WASD — движение   •   Пробел — пауза   •   R — заново   •   Esc — выход",
            bg=self.COLORS["bg"], fg=self.COLORS["hint"], font=("Segoe UI", 9),
        ).pack(pady=(8, 12))

        root.bind("<KeyPress>", self._on_key_press)
        self._draw()
        self._schedule_next()

    # -- ввод --------------------------------------------------------------

    def _on_key_press(self, event: tk.Event) -> None:
        key = (event.keysym or "").lower()

        if key == "escape":
            self.close()
            return
        if key == "r":
            self.game.reset()
            self._draw()
            return
        if key == "space":
            self.game.toggle_pause()
            self._draw()
            return

        direction = KEY_TO_DIRECTION.get(key)
        if direction is not None and self.game.set_direction(direction):
            self._draw()

    # -- отрисовка ---------------------------------------------------------

    def _draw(self) -> None:
        g = self.game
        self.canvas.delete("all")

        # Сетка
        for x in range(g.cols + 1):
            self.canvas.create_line(
                x * CELL_SIZE, 0, x * CELL_SIZE, g.rows * CELL_SIZE,
                fill=self.COLORS["grid"],
            )
        for y in range(g.rows + 1):
            self.canvas.create_line(
                0, y * CELL_SIZE, g.cols * CELL_SIZE, y * CELL_SIZE,
                fill=self.COLORS["grid"],
            )

        # Еда
        if g.food is not None:
            fx, fy = g.food
            pad = CELL_SIZE // 5
            self.canvas.create_oval(
                fx * CELL_SIZE + pad, fy * CELL_SIZE + pad,
                (fx + 1) * CELL_SIZE - pad, (fy + 1) * CELL_SIZE - pad,
                fill=self.COLORS["food"], outline="",
            )

        # Змейка (сначала хвост, чтобы голова оказалась сверху)
        last_index = len(g.snake) - 1
        for index, (x, y) in enumerate(reversed(g.snake)):
            is_head = index == last_index
            color = self.COLORS["head"] if is_head else self.COLORS["snake"]
            self.canvas.create_rectangle(
                x * CELL_SIZE + 1, y * CELL_SIZE + 1,
                (x + 1) * CELL_SIZE - 1, (y + 1) * CELL_SIZE - 1,
                fill=color, outline=self.COLORS["bg"],
            )

        # Глаза на голове
        if g.snake:
            self._draw_eyes(*g.head, g.direction)

        # Счёт
        self.score_label.configure(
            text=f"Счёт: {g.score}    Еда: {g.food_eaten}    Скорость: {g.speed_ms} мс"
        )

        # Сообщения поверх поля
        if g.over or g.won:
            self._draw_overlay(g.death_reason, f"Счёт: {g.score}", "R — начать заново")
        elif g.paused:
            self._draw_overlay("ПАУЗА", "Пробел — продолжить")

    def _draw_eyes(self, hx: int, hy: int, direction: Cell) -> None:
        dx, dy = direction
        cx = hx * CELL_SIZE + CELL_SIZE / 2
        cy = hy * CELL_SIZE + CELL_SIZE / 2
        offset = CELL_SIZE * 0.22
        forward = CELL_SIZE * 0.18
        pupil = 2.2

        eye_positions = [
            (cx + dx * forward - dy * offset, cy + dy * forward + dx * offset),
            (cx + dx * forward + dy * offset, cy + dy * forward - dx * offset),
        ]
        for ex, ey in eye_positions:
            self.canvas.create_oval(
                ex - pupil, ey - pupil, ex + pupil, ey + pupil,
                fill=self.COLORS["bg"], outline="",
            )

    def _draw_overlay(self, title: str, subtitle: str, hint: str = "") -> None:
        width = self.game.cols * CELL_SIZE
        height = self.game.rows * CELL_SIZE
        self.canvas.create_rectangle(
            0, 0, width, height, fill=self.COLORS["overlay"], stipple="gray50"
        )
        self.canvas.create_text(
            width / 2, height / 2 - 26, text=title,
            fill=self.COLORS["text"], font=("Segoe UI", 22, "bold"),
        )
        self.canvas.create_text(
            width / 2, height / 2 + 12, text=subtitle,
            fill=self.COLORS["snake"], font=("Segoe UI", 13, "bold"),
        )
        if hint:
            self.canvas.create_text(
                width / 2, height / 2 + 42, text=hint,
                fill=self.COLORS["hint"], font=("Segoe UI", 10),
            )

    # -- цикл --------------------------------------------------------------

    def _schedule_next(self) -> None:
        if self._closed:
            return
        self._timer = self.root.after(self.game.speed_ms, self._tick)

    def _tick(self) -> None:
        self.game.step()
        self._draw()
        self._schedule_next()

    def close(self) -> None:
        self._closed = True
        if self._timer is not None:
            try:
                self.root.after_cancel(self._timer)
            except tk.TclError:
                pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    SnakeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
