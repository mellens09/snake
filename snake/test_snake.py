"""Юнит-тесты для игровой логики «Змейки» (без графики).

Запуск:  python -m unittest test_snake -v
"""

import random
import unittest

from snake import DOWN, LEFT, RIGHT, UP, SnakeGame


def make_game(cols=10, rows=10, seed=1) -> SnakeGame:
    return SnakeGame(cols=cols, rows=rows, rng=random.Random(seed))


class TestStart(unittest.TestCase):
    def test_initial_state(self):
        game = make_game()
        self.assertEqual(len(game.snake), 3)
        self.assertEqual(game.score, 0)
        self.assertFalse(game.over)
        self.assertFalse(game.paused)
        self.assertIsNotNone(game.food)
        self.assertNotIn(game.food, game.snake)

    def test_reset_restores_state(self):
        game = make_game()
        game.score = 50
        game.over = True
        game.reset()
        self.assertEqual(game.score, 0)
        self.assertFalse(game.over)
        self.assertEqual(len(game.snake), 3)


class TestMovement(unittest.TestCase):
    def test_moves_forward(self):
        game = make_game()
        head = game.head
        game.step()
        self.assertEqual(game.head, (head[0] + 1, head[1]))
        self.assertEqual(len(game.snake), 3)

    def test_cannot_reverse(self):
        game = make_game()
        self.assertFalse(game.set_direction(LEFT))   # змейка смотрит вправо
        game.step()
        self.assertEqual(game.direction, RIGHT)

    def test_turn_applied_on_next_step(self):
        game = make_game()
        game.set_direction(DOWN)
        game.step()
        self.assertEqual(game.direction, DOWN)
        self.assertEqual(game.head, (game.cols // 2, game.rows // 2 + 1))

    def test_queued_turn_is_not_lost(self):
        game = make_game()
        game.set_direction(UP)
        game.step()
        game.set_direction(LEFT)
        game.step()
        self.assertEqual(game.direction, LEFT)

    def test_no_reverse_within_one_tick(self):
        # Регресс: «вправо → вверх → влево» не должно развернуть змейку в тело
        game = make_game()
        self.assertTrue(game.set_direction(UP))
        self.assertFalse(game.set_direction(LEFT))
        game.step()
        self.assertEqual(game.direction, UP)

    def test_pause_freezes_movement(self):
        game = make_game()
        game.toggle_pause()
        head = game.head
        game.step()
        self.assertEqual(game.head, head)
        self.assertTrue(game.paused)


class TestFood(unittest.TestCase):
    def test_eating_food_grows_and_scores(self):
        game = make_game()
        head = game.head
        game.food = (head[0] + 1, head[1])
        game.step()
        self.assertEqual(len(game.snake), 4)
        self.assertEqual(game.score, 10)
        self.assertEqual(game.food_eaten, 1)
        self.assertNotIn(game.food, game.snake)

    def test_speed_increases_with_food(self):
        game = make_game()
        start = game.speed_ms
        game.food = (game.head[0] + 1, game.head[1])
        game.step()
        self.assertLess(game.speed_ms, start)

    def test_food_never_spawns_on_snake(self):
        game = make_game(cols=5, rows=5)
        for _ in range(50):
            game.food = game._spawn_food()
            self.assertNotIn(game.food, game.snake)

    def test_full_board_means_win(self):
        game = make_game(cols=3, rows=3)
        # Голова в (0,1), тело занимает все клетки, кроме (1,1) — там еда
        game.snake = [
            (0, 1), (0, 0), (1, 0), (2, 0),
            (2, 1), (2, 2), (1, 2), (0, 2),
        ]
        game.direction = RIGHT
        game.next_direction = RIGHT
        game.food = (1, 1)
        game.step()
        self.assertTrue(game.won)
        self.assertIsNone(game.food)
        self.assertEqual(game.score, 10)
        self.assertEqual(len(game.snake), 9)


class TestCollisions(unittest.TestCase):
    def test_wall_collision_ends_game(self):
        game = make_game(cols=5, rows=5)
        game.snake = [(4, 2), (3, 2), (2, 2)]
        game.direction = RIGHT
        game.next_direction = RIGHT
        game.food = (0, 0)
        game.step()
        self.assertTrue(game.over)
        self.assertIn("стен", game.death_reason.lower())

    def test_self_collision_ends_game(self):
        game = make_game(cols=5, rows=5)
        # Голова в (1,2) движется вправо прямо в клетку (2,2) своего тела
        game.snake = [
            (1, 2), (1, 1), (2, 1), (2, 2),
            (2, 3), (3, 3), (3, 2),
        ]
        game.direction = RIGHT
        game.next_direction = RIGHT
        game.food = (0, 0)
        game.step()
        self.assertTrue(game.over)
        self.assertIn("собой", game.death_reason.lower())

    def test_step_after_game_over_does_nothing(self):
        game = make_game(cols=5, rows=5)
        game.snake = [(4, 2), (3, 2), (2, 2)]
        game.direction = RIGHT
        game.next_direction = RIGHT
        game.food = (0, 0)
        game.step()
        self.assertTrue(game.over)
        snake_before = list(game.snake)
        game.step()
        self.assertEqual(game.snake, snake_before)


class TestSpeed(unittest.TestCase):
    def test_speed_has_lower_bound(self):
        game = make_game()
        game.food_eaten = 1000
        self.assertGreaterEqual(game.speed_ms, 55)

    def test_speed_decreases_monotonically(self):
        game = make_game()
        previous = game.speed_ms
        for _ in range(20):
            game.food_eaten += 1
            self.assertLessEqual(game.speed_ms, previous)
            previous = game.speed_ms


if __name__ == "__main__":
    unittest.main()
