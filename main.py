import arcade
import random
import sqlite3

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Traffic Racer Lite"

PLAYER_SPEED = 5.0
ENEMY_SPEED_MIN = 3.0
ENEMY_SPEED_MAX = 4.5
ROAD_SPEED_BASE = PLAYER_SPEED
ENEMY_COUNT = 8
ROAD_LINE_COUNT = 10
SCORE_INCREMENT = 1
GAME_OVER_DURATION = 2
SPEED_INCREASE_INTERVAL = 15
SPEED_INCREASE_AMOUNT = 0.05


class Database:
    @staticmethod
    def connect():
        return sqlite3.connect("carsgame.db")

    @staticmethod
    def register_or_login_user(username, password):
        conn = Database.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                conn.close()

                if user:
                    return user[0]
                else:
                    return None
            else:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                id = cursor.lastrowid
                conn.commit()
                conn.close()
                return id
        except sqlite3.OperationalError as e:
            print(f"Ошибка базы данных: {e}")
            conn.close()
            return None
        except Exception as e:
            print(f"Ошибка: {e}")
            conn.close()
            return None

    @staticmethod
    def save_record(id, score):
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO records (id, score) VALUES (?, ?)", (id, score))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при сохранении рекорда: {e}")
            return False

    @staticmethod
    def get_top_players(limit=5):
        try:
            conn = Database.connect()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT u.username, MAX(r.score) as max_score
                FROM users u
                JOIN records r ON u.id = r.id
                GROUP BY u.id
                ORDER BY max_score DESC
                LIMIT ?
            ''', (limit,))

            results = cursor.fetchall()
            conn.close()

            leaderboard = []
            for row in results:
                leaderboard.append({
                    "name": row[0],
                    "score": row[1]
                })

            return leaderboard
        except Exception as e:
            print(f"Ошибка при получении таблицы лидеров: {e}")
            return []


class RegistrationWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Регистрация - Traffic Racer Lite")

        self.player_name = ""
        self.password = ""
        self.active_field = "name"
        self.game_window = None
        self.error_message = ""
        self.error_timer = 0

        self.leaderboard = Database.get_top_players(5)

        arcade.set_background_color((30, 30, 40))

    def setup(self):
        self.player_name = ""
        self.password = ""
        self.active_field = "name"
        self.error_message = ""
        self.error_timer = 0
        self.leaderboard = Database.get_top_players(5)

    def draw_rectangle(self, center_x, center_y, width, height, color):
        left = center_x - width / 2
        right = center_x + width / 2
        bottom = center_y - height / 2
        top = center_y + height / 2

        arcade.draw_polygon_filled([
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top)
        ], color)

    def draw_rectangle_outline(self, center_x, center_y, width, height, color, border_width):
        left = center_x - width / 2
        right = center_x + width / 2
        bottom = center_y - height / 2
        top = center_y + height / 2

        arcade.draw_polygon_outline([
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top)
        ], color, border_width)

    def on_draw(self):
        self.clear()

        self.draw_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                            SCREEN_WIDTH, SCREEN_HEIGHT, (20, 20, 30))

        arcade.draw_text("РЕГИСТРАЦИЯ ИГРОКА", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
                         arcade.color.GOLD, 28, anchor_x="center",
                         font_name="Arial", bold=True)

        self.draw_registration_form()

        self.draw_leaderboard()

        arcade.draw_text("TAB - переключение полей | ENTER - вход | ESC - выход",
                         SCREEN_WIDTH // 2, 25, arcade.color.LIGHT_YELLOW,
                         14, anchor_x="center", font_name="Arial")

        if self.error_message and self.error_timer > 0:
            arcade.draw_text(self.error_message, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150,
                             arcade.color.RED, 16, anchor_x="center", font_name="Arial")

    def draw_registration_form(self):
        form_x = SCREEN_WIDTH // 4
        form_start_y = SCREEN_HEIGHT - 130

        arcade.draw_text("ВХОД В ИГРУ", form_x, form_start_y,
                         arcade.color.CYAN, 22, anchor_x="center",
                         font_name="Arial", bold=True)

        y_position = form_start_y - 50

        arcade.draw_text("Имя:", form_x - 120, y_position - 5,
                         arcade.color.WHITE, 16, anchor_x="right",
                         font_name="Arial")

        field_color = (100, 180, 255) if self.active_field == "name" else arcade.color.WHITE
        field_width = 250
        field_height = 35
        self.draw_rectangle(form_x + 40, y_position, field_width, field_height, (40, 40, 50))
        self.draw_rectangle_outline(form_x + 40, y_position, field_width, field_height, field_color, 2)

        display_name = self.player_name if self.player_name else "Введите имя..."
        name_color = arcade.color.WHITE if self.player_name else (150, 150, 150)
        arcade.draw_text(display_name, form_x + 40 - field_width / 2 + 10, y_position,
                         name_color, 16, anchor_y="center",
                         font_name="Arial", width=field_width - 20)

        y_position -= 60

        arcade.draw_text("Пароль:", form_x - 110, y_position - 5,
                         arcade.color.WHITE, 16, anchor_x="right",
                         font_name="Arial")

        field_color = (100, 180, 255) if self.active_field == "password" else arcade.color.WHITE
        self.draw_rectangle(form_x + 40, y_position, field_width, field_height, (40, 40, 50))
        self.draw_rectangle_outline(form_x + 40, y_position, field_width, field_height, field_color, 2)

        display_password = "*" * len(self.password) if self.password else "Введите пароль..."
        password_color = arcade.color.WHITE if self.password else (150, 150, 150)
        arcade.draw_text(display_password, form_x + 40 - field_width / 2 + 10, y_position,
                         password_color, 16, anchor_y="center",
                         font_name="Arial", width=field_width - 20)

        y_position -= 70
        button_width = 180
        button_height = 40

        button_color = (0, 120, 0) if self.player_name and self.password else (60, 60, 70)
        self.draw_rectangle(form_x, y_position, button_width, button_height, button_color)
        self.draw_rectangle_outline(form_x, y_position, button_width, button_height, arcade.color.LIME_GREEN, 2)

        button_text_color = arcade.color.WHITE if self.player_name and self.password else (120, 120, 120)
        arcade.draw_text("ВОЙТИ", form_x, y_position,
                         button_text_color, 18, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

    def draw_leaderboard(self):
        leaderboard_x = SCREEN_WIDTH - SCREEN_WIDTH // 4
        leaderboard_start_y = SCREEN_HEIGHT - 130

        arcade.draw_text("ТАБЛИЦА ЛИДЕРОВ", leaderboard_x, leaderboard_start_y,
                         arcade.color.CYAN, 22, anchor_x="center",
                         font_name="Arial", bold=True)

        table_width = 320
        table_height = 320
        table_y = leaderboard_start_y - 40 - table_height / 2

        self.draw_rectangle_outline(leaderboard_x, table_y,
                                    table_width, table_height,
                                    (100, 150, 255), 2)

        header_y = leaderboard_start_y - 45

        arcade.draw_text("№", leaderboard_x - 110, header_y - -7,
                         arcade.color.YELLOW, 14, anchor_x="center",
                         font_name="Arial", bold=True)

        arcade.draw_text("Игрок", leaderboard_x - 30, header_y - -7,
                         arcade.color.YELLOW, 14, anchor_x="center",
                         font_name="Arial", bold=True)

        arcade.draw_text("Очки", leaderboard_x + 70, header_y - -7,
                         arcade.color.YELLOW, 14, anchor_x="center",
                         font_name="Arial", bold=True)

        line_y = header_y - 10
        arcade.draw_line(leaderboard_x - table_width / 2 + 10, line_y,
                         leaderboard_x + table_width / 2 - 10, line_y,
                         arcade.color.WHITE, 1)

        y_position = line_y - 25

        if not self.leaderboard:
            self.draw_rectangle(leaderboard_x, y_position - 35 / 2,
                                table_width - 20, 35, (40, 40, 60))
            arcade.draw_text("Нет данных", leaderboard_x, y_position,
                             arcade.color.LIGHT_GRAY, 16, anchor_x="center", anchor_y="center",
                             font_name="Arial")
            y_position -= 40
        else:
            for i, player in enumerate(self.leaderboard, 1):
                row_color = (40, 40, 60) if i % 2 == 1 else (50, 50, 70)
                row_height = 35
                self.draw_rectangle(leaderboard_x, y_position - row_height / 2,
                                    table_width - 20, row_height, row_color)

                if i == 1:
                    place_color = arcade.color.GOLD
                elif i == 2:
                    place_color = arcade.color.SILVER
                elif i == 3:
                    place_color = (205, 127, 50)
                else:
                    place_color = arcade.color.WHITE

                arcade.draw_text(f"{i}.", leaderboard_x - 110, y_position,
                                 place_color, 14, anchor_x="center", anchor_y="center",
                                 font_name="Arial", bold=(i <= 3))

                player_name = player["name"]
                if len(player_name) > 10:
                    player_name = player_name[:8] + ".."

                arcade.draw_text(player_name, leaderboard_x - 30, y_position,
                                 arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
                                 font_name="Arial")

                arcade.draw_text(str(player["score"]), leaderboard_x + 70, y_position,
                                 arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
                                 font_name="Arial")

                y_position -= row_height + 5

        arcade.draw_text("Топ-5 игроков", leaderboard_x, y_position - 10,
                         arcade.color.LIGHT_GRAY, 12, anchor_x="center",
                         font_name="Arial")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            if self.player_name and self.password:
                id = Database.register_or_login_user(self.player_name, self.password)

                if id:
                    self.close()
                    game_window = MyGame(self.player_name, id)
                    game_window.setup()
                    arcade.run()
                else:
                    self.player_name = ""
                    self.password = ""
                    self.active_field = "name"
                    self.error_message = "Неверный пароль!"
                    self.error_timer = 3
            elif not self.player_name:
                self.active_field = "name"
                self.error_message = "Введите имя пользователя!"
                self.error_timer = 2
            elif not self.password:
                self.active_field = "password"
                self.error_message = "Введите пароль!"
                self.error_timer = 2
        elif key == arcade.key.TAB:
            if self.active_field == "name":
                self.active_field = "password"
            else:
                self.active_field = "name"
        elif key == arcade.key.BACKSPACE:
            if self.active_field == "name" and self.player_name:
                self.player_name = self.player_name[:-1]
            elif self.active_field == "password" and self.password:
                self.password = self.password[:-1]
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_key_release(self, symbol, modifiers):
        pass

    def on_text(self, text):
        if self.active_field == "name":
            if text.isalnum() or text.isspace():
                if len(self.player_name) < 12:
                    self.player_name += text
        elif self.active_field == "password":
            if text != " " and len(text) == 1:
                if len(self.password) < 16:
                    self.password += text

    def update(self, delta_time):
        if self.error_timer > 0:
            self.error_timer -= delta_time
            if self.error_timer <= 0:
                self.error_message = ""


class PlayerCar:
    def __init__(self):
        self.color = (0, 150, 255)
        self.glow_color = (100, 200, 255)
        self.width = 40
        self.height = 70
        self.speed = PLAYER_SPEED

    def draw(self, center_x, center_y):
        glow_size = 10
        left = center_x - (self.width + glow_size) / 2
        right = center_x + (self.width + glow_size) / 2
        bottom = center_y - (self.height + glow_size) / 2
        top = center_y + (self.height + glow_size) / 2

        arcade.draw_polygon_filled([
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top)
        ], self.glow_color)

        left = center_x - self.width / 2
        right = center_x + self.width / 2
        bottom = center_y - self.height / 2
        top = center_y + self.height / 2

        arcade.draw_polygon_filled([
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top)
        ], self.color)

        windshield_left = center_x - (self.width - 10) / 2
        windshield_right = center_x + (self.width - 10) / 2
        windshield_bottom = center_y + 7.5
        windshield_top = center_y + 22.5

        arcade.draw_polygon_filled([
            (windshield_left, windshield_bottom),
            (windshield_right, windshield_bottom),
            (windshield_right, windshield_top),
            (windshield_left, windshield_top)
        ], (200, 230, 255))

        arcade.draw_polygon_filled([
            (center_x - 19, center_y + self.height / 2 - 7.5),
            (center_x - 11, center_y + self.height / 2 - 7.5),
            (center_x - 11, center_y + self.height / 2 - 2.5),
            (center_x - 19, center_y + self.height / 2 - 2.5)
        ], (255, 255, 200))

        arcade.draw_polygon_filled([
            (center_x + 11, center_y + self.height / 2 - 7.5),
            (center_x + 19, center_y + self.height / 2 - 7.5),
            (center_x + 19, center_y + self.height / 2 - 2.5),
            (center_x + 11, center_y + self.height / 2 - 2.5)
        ], (255, 255, 200))

        arcade.draw_polygon_filled([
            (center_x - 19, center_y - self.height / 2 + 2.5),
            (center_x - 11, center_y - self.height / 2 + 2.5),
            (center_x - 11, center_y - self.height / 2 + 7.5),
            (center_x - 19, center_y - self.height / 2 + 7.5)
        ], (255, 50, 50))

        arcade.draw_polygon_filled([
            (center_x + 11, center_y - self.height / 2 + 2.5),
            (center_x + 19, center_y - self.height / 2 + 2.5),
            (center_x + 19, center_y - self.height / 2 + 7.5),
            (center_x + 11, center_y - self.height / 2 + 7.5)
        ], (255, 50, 50))


class EnemyCar:
    def __init__(self, lane, road_left, road_right):
        self.colors = [
            (255, 80, 80), (255, 180, 50), (100, 220, 100), (180, 180, 220),
            (255, 100, 180), (180, 100, 255), (80, 200, 220), (220, 220, 100)
        ]
        self.color = random.choice(self.colors)
        self.width = 36
        self.height = 65
        self.lane = lane
        self.road_left = road_left
        self.road_right = road_right
        self.base_speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
        self.reset_position()

    def reset_position(self):
        road_width = self.road_right - self.road_left
        lane_width = road_width / 4
        self.center_x = self.road_left + (self.lane + 0.5) * lane_width
        self.center_y = SCREEN_HEIGHT + random.uniform(100, 500)
        self.base_speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)

    def draw(self):
        left = self.center_x - self.width / 2
        right = self.center_x + self.width / 2
        bottom = self.center_y - self.height / 2
        top = self.center_y + self.height / 2

        arcade.draw_polygon_filled([
            (left, bottom),
            (right, bottom),
            (right, top),
            (left, top)
        ], self.color)

        windshield_left = self.center_x - (self.width - 8) / 2
        windshield_right = self.center_x + (self.width - 8) / 2
        windshield_bottom = self.center_y + 6
        windshield_top = self.center_y + 18

        arcade.draw_polygon_filled([
            (windshield_left, windshield_bottom),
            (windshield_right, windshield_bottom),
            (windshield_right, windshield_top),
            (windshield_left, windshield_top)
        ], (230, 240, 250))

        arcade.draw_polygon_filled([
            (self.center_x - 15, self.center_y + self.height / 2 - 6),
            (self.center_x - 9, self.center_y + self.height / 2 - 6),
            (self.center_x - 9, self.center_y + self.height / 2 - 2),
            (self.center_x - 15, self.center_y + self.height / 2 - 2)
        ], (255, 255, 180))

        arcade.draw_polygon_filled([
            (self.center_x + 9, self.center_y + self.height / 2 - 6),
            (self.center_x + 15, self.center_y + self.height / 2 - 6),
            (self.center_x + 15, self.center_y + self.height / 2 - 2),
            (self.center_x + 9, self.center_y + self.height / 2 - 2)
        ], (255, 255, 180))

    def update(self, delta_time, enemy_cars, speed_multiplier=1.0):
        effective_speed = self.base_speed * speed_multiplier
        self.center_y -= effective_speed * delta_time * 60

        for enemy in enemy_cars:
            if enemy != self and enemy.lane == self.lane:
                distance_y = abs(self.center_y - enemy.center_y)
                if distance_y < self.height + 50:
                    self.base_speed = min(self.base_speed, enemy.base_speed * 0.9)
                    if random.random() < 0.02:
                        shift = random.uniform(-10, 10)
                        new_x = self.center_x + shift
                        if (new_x - self.width / 2 > self.road_left and
                                new_x + self.width / 2 < self.road_right):
                            self.center_x = new_x

        if self.center_y < -150:
            self.reset_position()


class MyGame(arcade.Window):
    def __init__(self, player_name, id):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.player_name = player_name
        self.id = id
        self.player = None
        self.enemy_cars = []
        self.road_lines = []
        self.score = 0
        self.game_over = False
        self.game_over_time = 0
        self.score_saved = False
        self.left_pressed = False
        self.right_pressed = False
        self.game_time = 0
        self.speed_multiplier = 1.0
        self.last_speed_increase_time = 0
        arcade.set_background_color((40, 40, 50))

        self.road_left = 180
        self.road_right = 620
        self.road_width = self.road_right - self.road_left
        self.road_center_x = (self.road_left + self.road_right) // 2

    def setup(self):
        self.player = PlayerCar()
        self.player_center_x = self.road_center_x
        self.player_center_y = 120

        self.enemy_cars = []
        for lane in range(4):
            for i in range(2):
                enemy = EnemyCar(lane, self.road_left, self.road_right)
                enemy.center_y = SCREEN_HEIGHT + 200 * i + random.uniform(0, 200)
                self.enemy_cars.append(enemy)

        self.road_lines = []
        line_spacing = SCREEN_HEIGHT // 20
        for i in range(20):
            self.road_lines.append({'y': i * line_spacing, 'speed': ROAD_SPEED_BASE})

        self.score = 0
        self.game_over = False
        self.game_over_time = 0
        self.score_saved = False
        self.left_pressed = False
        self.right_pressed = False
        self.game_time = 0
        self.speed_multiplier = 1.0
        self.last_speed_increase_time = 0

    def draw_rectangle(self, center_x, center_y, width, height, color):
        left = center_x - width / 2
        right = center_x + width / 2
        bottom = center_y - height / 2
        top = center_y + height / 2
        arcade.draw_polygon_filled([
            (left, bottom), (right, bottom), (right, top), (left, top)
        ], color)

    def draw_road_line(self, center_x, y, width, height, color):
        left = center_x - width / 2
        right = center_x + width / 2
        bottom = y - height / 2
        top = y + height / 2
        arcade.draw_polygon_filled([
            (left, bottom), (right, bottom), (right, top), (left, top)
        ], color)

    def on_draw(self):
        self.clear()

        self.draw_rectangle(self.road_center_x, SCREEN_HEIGHT // 2,
                            self.road_width, SCREEN_HEIGHT, (50, 50, 50))

        self.draw_rectangle(self.road_left // 2, SCREEN_HEIGHT // 2,
                            self.road_left, SCREEN_HEIGHT, (40, 80, 40))
        self.draw_rectangle(SCREEN_WIDTH - self.road_left // 2, SCREEN_HEIGHT // 2,
                            self.road_left, SCREEN_HEIGHT, (40, 80, 40))

        line_width = 8
        line_height = 40
        for line in self.road_lines:
            self.draw_road_line(self.road_center_x, line['y'],
                                line_width, line_height, (255, 255, 200))

        lane_width = self.road_width // 4
        lane_markers_x = [
            self.road_left + lane_width,
            self.road_left + 2 * lane_width,
            self.road_left + 3 * lane_width
        ]
        for marker_x in lane_markers_x:
            for line in self.road_lines:
                self.draw_road_line(marker_x, line['y'] + 20, 4, 20, (200, 200, 200))

        for enemy in self.enemy_cars:
            enemy.draw()

        self.player.draw(self.player_center_x, self.player_center_y)

        arcade.draw_line(self.road_left, 0, self.road_left, SCREEN_HEIGHT,
                         (255, 255, 255), 2)
        arcade.draw_line(self.road_right, 0, self.road_right, SCREEN_HEIGHT,
                         (255, 255, 255), 2)

        arcade.draw_line(self.road_left, 0, self.road_left, SCREEN_HEIGHT,
                         (255, 255, 100), 2)
        arcade.draw_line(self.road_right, 0, self.road_right, SCREEN_HEIGHT,
                         (255, 255, 100), 2)

        player_text = f"ИГРОК: {self.player_name}"
        arcade.draw_text(player_text, 15, SCREEN_HEIGHT - 35,
                         (100, 200, 255), 20, font_name="Arial", bold=True)

        score_text = f"СЧЁТ: {self.score}"
        arcade.draw_text(score_text, 15, SCREEN_HEIGHT - 70,
                         (255, 255, 255), 24, font_name="Arial", bold=True)

        speed_text = f"СКОРОСТЬ: x{self.speed_multiplier:.2f}"
        arcade.draw_text(speed_text, 15, SCREEN_HEIGHT - 105,
                         (255, 200, 100), 20, font_name="Arial", bold=True)

        time_text = f"ВРЕМЯ: {int(self.game_time)}с"
        arcade.draw_text(time_text, 15, SCREEN_HEIGHT - 140,
                         (100, 255, 200), 20, font_name="Arial", bold=True)

        instructions = "← → ДВИЖЕНИЕ | R РЕСТАРТ | ESC МЕНЮ"
        arcade.draw_text(instructions, SCREEN_WIDTH // 2, 30,
                         (200, 200, 255), 16, anchor_x="center",
                         font_name="Arial", bold=True)

        if self.game_over:
            self.draw_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 180))

            arcade.draw_text("ИГРА ОКОНЧЕНА", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60,
                             (255, 80, 80), 48, anchor_x="center", anchor_y="center",
                             font_name="Arial", bold=True)
            arcade.draw_text(f"Игрок: {self.player_name}", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 + 10, (100, 200, 255), 32,
                             anchor_x="center", anchor_y="center", font_name="Arial", bold=True)
            arcade.draw_text(f"Счёт: {self.score}", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 40, (255, 255, 255), 36,
                             anchor_x="center", anchor_y="center", font_name="Arial", bold=True)

            if self.score_saved:
                save_text = "✓ Результат сохранён"
                save_color = (100, 255, 100)
            else:
                save_text = "Сохранение результата..."
                save_color = (255, 255, 100)

            arcade.draw_text(save_text, SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 90, save_color, 22,
                             anchor_x="center", anchor_y="center", font_name="Arial")

            arcade.draw_text("ПРОБЕЛ - НОВАЯ ИГРА", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 140, (255, 255, 200), 20,
                             anchor_x="center", anchor_y="center", font_name="Arial", bold=True)
            arcade.draw_text("ESC - ВЫХОД В МЕНЮ", SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2 - 180, (255, 255, 200), 20,
                             anchor_x="center", anchor_y="center", font_name="Arial", bold=True)

    def on_update(self, delta_time):
        if self.game_over:
            if not self.score_saved:
                if Database.save_record(self.id, self.score):
                    self.score_saved = True
            self.game_over_time += delta_time
            return

        self.game_time += delta_time

        if self.game_time - self.last_speed_increase_time >= SPEED_INCREASE_INTERVAL:
            self.speed_multiplier += SPEED_INCREASE_AMOUNT
            self.last_speed_increase_time = self.game_time

        road_width = self.road_right - self.road_left
        lane_width = road_width / 4
        lanes_x = [self.road_left + (i + 0.5) * lane_width for i in range(4)]

        if self.left_pressed and self.player_center_x > self.road_left + self.player.width // 2:
            self.player_center_x -= self.player.speed
            nearest_lane = min(lanes_x, key=lambda x: abs(x - self.player_center_x))
            if abs(self.player_center_x - nearest_lane) < 5:
                self.player_center_x = nearest_lane

        if self.right_pressed and self.player_center_x < self.road_right - self.player.width // 2:
            self.player_center_x += self.player.speed
            nearest_lane = min(lanes_x, key=lambda x: abs(x - self.player_center_x))
            if abs(self.player_center_x - nearest_lane) < 5:
                self.player_center_x = nearest_lane

        for line in self.road_lines:
            line['y'] -= line['speed'] * self.speed_multiplier
            if line['y'] < -40:
                max_y = max(l['y'] for l in self.road_lines)
                line['y'] = max_y + 40

        for enemy in self.enemy_cars:
            enemy.update(delta_time, self.enemy_cars, self.speed_multiplier)

        for enemy in self.enemy_cars:
            player_left = self.player_center_x - self.player.width // 2
            player_right = self.player_center_x + self.player.width // 2
            player_top = self.player_center_y + self.player.height // 2
            player_bottom = self.player_center_y - self.player.height // 2

            enemy_left = enemy.center_x - enemy.width // 2
            enemy_right = enemy.center_x + enemy.width // 2
            enemy_top = enemy.center_y + enemy.height // 2
            enemy_bottom = enemy.center_y - enemy.height // 2

            if (player_right > enemy_left and player_left < enemy_right and
                    player_bottom < enemy_top and player_top > enemy_bottom):
                self.game_over = True
                break

        self.score += int(self.speed_multiplier)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            if self.game_over:
                self.setup()
        elif key == arcade.key.R:
            self.setup()
        elif key == arcade.key.ESCAPE:
            self.close()
            window = RegistrationWindow()
            window.setup()
            arcade.run()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False


def main():
    window = RegistrationWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()