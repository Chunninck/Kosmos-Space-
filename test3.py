import pygame
import math
import sys
import random

# Инициализация
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Космическая гравитация с коллизиями")
clock = pygame.time.Clock()

# Константы
G = 6.67  # Гравитационная постоянная
COLLISION_DAMPING = 0.8  # Коэффициент упругости (1 - упругое, 0 - неупругое)

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_BLUE = (100, 150, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

class Particle:
    """Класс для частиц взрыва"""
    def __init__(self, x, y, vx, vy, color, size, lifetime=60):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.vx *= 0.99
        self.vy *= 0.99
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            
    def draw(self, screen):
        if not self.alive:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class Body:
    def __init__(self, x, y, vx=0, vy=0, mass=50, color=RED, radius=20, is_fixed=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        self.color = color
        self.radius = radius
        self.alive = True
        self.trail = []
        self.is_fixed = is_fixed
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.is_selected = False  # Выбран ли объект для отображения параметров
        
        # Орбитальные параметры (рассчитываются)
        self.orbit_radius = 0
        self.orbit_speed = 0
        self.orbit_period = 0
        self.orbit_angle = 0
        self.eccentricity = 0
        self.orbital_energy = 0
        
    def update_position(self):
        if self.is_fixed or self.is_dragging:
            return
        self.x += self.vx
        self.y += self.vy
        
    def apply_gravity(self, other):
        if self.is_fixed and other.is_fixed:
            return
        if self.is_dragging or other.is_dragging:
            return
            
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 1:
            distance = 1
            
        force = G * self.mass * other.mass / (distance ** 2)
        fx = dx / distance
        fy = dy / distance
        
        ax = force * fx / self.mass
        ay = force * fy / self.mass
        
        if not self.is_fixed:
            self.vx += ax
            self.vy += ay
        
        if not other.is_fixed:
            other.vx -= ax * (self.mass / other.mass)
            other.vy -= ay * (self.mass / other.mass)
            
    def calculate_orbit_params(self, center):
        """Расчет орбитальных параметров относительно центра"""
        if self.is_fixed or not self.alive:
            return
            
        dx = self.x - center.x
        dy = self.y - center.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 1:
            return
            
        # Скорость
        speed = math.sqrt(self.vx**2 + self.vy**2)
        
        # Радиус орбиты (среднее расстояние)
        self.orbit_radius = distance
        
        # Орбитальная скорость (тангенциальная)
        # Находим тангенциальную составляющую скорости
        radial_v = (self.vx * dx + self.vy * dy) / distance
        tangent_vx = self.vx - radial_v * dx / distance
        tangent_vy = self.vy - radial_v * dy / distance
        self.orbit_speed = math.sqrt(tangent_vx**2 + tangent_vy**2)
        
        # Период (T = 2*pi*r/v)
        if self.orbit_speed > 0.01:
            self.orbit_period = 2 * math.pi * distance / self.orbit_speed
        else:
            self.orbit_period = float('inf')
        
        # Угол орбиты
        self.orbit_angle = math.atan2(dy, dx)
        
        # Эксцентриситет (приблизительный)
        # Используем соотношение скоростей
        circular_speed = math.sqrt(G * center.mass / distance)
        if circular_speed > 0:
            self.eccentricity = abs(1 - self.orbit_speed / circular_speed)
        else:
            self.eccentricity = 0
            
        # Орбитальная энергия (на единицу массы)
        kinetic = 0.5 * speed**2
        potential = -G * center.mass / distance
        self.orbital_energy = kinetic + potential
        
    def check_collision(self, other):
        if not self.alive or not other.alive:
            return False
        if self.is_fixed and other.is_fixed:
            return False
        if self.is_dragging or other.is_dragging:
            return False
            
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        min_distance = self.get_radius() + other.get_radius()
        
        if distance < min_distance:
            self.resolve_collision(other)
            return True
        return False
    
    def create_explosion(self, other):
        particles = []
        cx = (self.x + other.x) / 2
        cy = (self.y + other.y) / 2
        
        num_particles = int((self.mass + other.mass) / 5) + 20
        num_particles = min(num_particles, 100)
        
        explosion_colors = [
            RED, ORANGE, YELLOW, (255, 200, 0),
            (255, 100, 0), (200, 50, 0), WHITE
        ]
        
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 15)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 8)
            color = random.choice(explosion_colors)
            offset_x = random.uniform(-20, 20)
            offset_y = random.uniform(-20, 20)
            lifetime = random.randint(20, 60)
            
            particles.append(Particle(
                cx + offset_x, cy + offset_y,
                vx, vy, color, size, lifetime
            ))
        
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 10)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 5)
            color = (150, 150, 150)
            lifetime = random.randint(30, 80)
            particles.append(Particle(
                cx + random.uniform(-10, 10),
                cy + random.uniform(-10, 10),
                vx, vy, color, size, lifetime
            ))
        
        return particles
    
    def resolve_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            if not self.is_fixed:
                self.x += random.uniform(-5, 5)
                self.y += random.uniform(-5, 5)
            if not other.is_fixed:
                other.x += random.uniform(-5, 5)
                other.y += random.uniform(-5, 5)
            return
            
        nx = dx / distance
        ny = dy / distance
        
        if self.is_fixed or other.is_fixed:
            moving = other if self.is_fixed else self
            fixed = self if self.is_fixed else other
            
            overlap = (self.get_radius() + other.get_radius() - distance)
            moving.x += overlap * (nx if moving == other else -nx)
            moving.y += overlap * (ny if moving == other else -ny)
            
            speed = math.sqrt(moving.vx**2 + moving.vy**2)
            if speed > 0:
                vn = moving.vx * nx + moving.vy * ny
                moving.vx -= 2 * vn * nx * COLLISION_DAMPING
                moving.vy -= 2 * vn * ny * COLLISION_DAMPING
            
            if fixed.is_fixed and not moving.is_fixed:
                moving.alive = False
            return
            
        if not self.is_fixed and not other.is_fixed:
            particles = self.create_explosion(other)
            global explosion_particles
            explosion_particles.extend(particles)
            self.alive = False
            other.alive = False
            return
        
        dvx = self.vx - other.vx
        dvy = self.vy - other.vy
        dvn = dvx * nx + dvy * ny
        
        if dvn > 0:
            return
            
        e = COLLISION_DAMPING
        j = -(1 + e) * dvn / (1/self.mass + 1/other.mass)
        
        self.vx += (j / self.mass) * nx
        self.vy += (j / self.mass) * ny
        other.vx -= (j / other.mass) * nx
        other.vy -= (j / other.mass) * ny
        
        overlap = (self.get_radius() + other.get_radius() - distance) / 2
        self.x -= overlap * nx
        self.y -= overlap * ny
        other.x += overlap * nx
        other.y += overlap * ny
        
        if e < 0.3 and self.mass > other.mass * 1.5:
            self.merge_with(other)
    
    def merge_with(self, other):
        total_mass = self.mass + other.mass
        self.vx = (self.vx * self.mass + other.vx * other.mass) / total_mass
        self.vy = (self.vy * self.mass + other.vy * other.mass) / total_mass
        self.mass = total_mass
        
        self.x = (self.x * self.mass + other.x * other.mass) / total_mass
        self.y = (self.y * self.mass + other.y * other.mass) / total_mass
        
        self.update_color()
        other.alive = False
        
    def update_color(self):
        if self.mass > 300:
            self.color = YELLOW
        elif self.mass > 200:
            self.color = ORANGE
        elif self.mass > 100:
            self.color = RED
        elif self.mass > 50:
            self.color = PURPLE
        else:
            self.color = BLUE
        
    def get_radius(self):
        return max(5, self.radius * (self.mass ** (1/3)) / 3.7)
    
    def is_clicked(self, mouse_x, mouse_y):
        if not self.alive:
            return False
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        return math.sqrt(dx**2 + dy**2) < self.get_radius() + 20
        
    def start_drag(self, mouse_x, mouse_y):
        if not self.alive:
            return
        self.is_dragging = True
        self.drag_offset_x = self.x - mouse_x
        self.drag_offset_y = self.y - mouse_y
        
    def update_drag(self, mouse_x, mouse_y):
        if self.is_dragging:
            self.x = mouse_x + self.drag_offset_x
            self.y = mouse_y + self.drag_offset_y
            self.vx = 0
            self.vy = 0
            
    def stop_drag(self):
        
        self.is_dragging = False
        
    def draw(self, screen):
        if not self.alive:
            return
            
        rad = self.get_radius()
        
        # Если объект выбран, рисуем орбитальную линию
        if self.is_selected and not self.is_fixed:
            # Рисуем круговую орбиту (приблизительно)
            if self.orbit_radius > 10:
                pygame.draw.circle(screen, CYAN, 
                                 (int(star.x), int(star.y)), 
                                 int(self.orbit_radius), 1)
                # Рисуем направление скорости
                speed_scale = 5
                end_x = self.x + self.vx * speed_scale
                end_y = self.y + self.vy * speed_scale
                pygame.draw.line(screen, GREEN, (self.x, self.y), (end_x, end_y), 2)
        
        # Свечение для массивных объектов
        if self.mass > 100:
            for i in range(3, 0, -1):
                glow_rad = rad + i * 10
                pygame.draw.circle(screen, self.color, 
                                 (int(self.x), int(self.y)), 
                                 int(glow_rad), 1)
        
        # Если объект перетаскивается, рисуем подсветку
        if self.is_dragging:
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x), int(self.y)), int(rad + 5), 3)
        
        # Рамка для выбранного объекта
        if self.is_selected:
            pygame.draw.circle(screen, MAGENTA, (int(self.x), int(self.y)), int(rad + 8), 3)
        
        # Рамка для фиксированных объектов
        if self.is_fixed:
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(rad), 2)
        
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(rad))
        
        # Отображаем массу
        if self.mass > 10:
            font = pygame.font.Font(None, 16)
            mass_text = font.render(f"{int(self.mass)}", True, WHITE)
            text_rect = mass_text.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(mass_text, text_rect)

# Создаем объекты
star = Body(WIDTH//2, HEIGHT//2, vx=0, vy=0, mass=400, color=YELLOW, radius=10, is_fixed=True)

planet1 = Body(
    WIDTH//2 + 200, 
    HEIGHT//2, 
    vx=0, 
    vy=3.2, 
    mass=30, 
    color=BLUE, 
    radius=15
)

planet2 = Body(
    WIDTH//2 - 250, 
    HEIGHT//2 + 50, 
    vx=0, 
    vy=-2.8, 
    mass=25, 
    color=GREEN, 
    radius=12
)

planet3 = Body(
    WIDTH//2 + 100, 
    HEIGHT//2 - 300, 
    vx=4.5, 
    vy=1.5, 
    mass=15, 
    color=RED, 
    radius=10
)

# Добавляем несколько маленьких астероидов
asteroids = []
for i in range(10):
    angle = random.uniform(0, 2 * math.pi)
    dist = random.uniform(100, 350)
    x = WIDTH//2 + dist * math.cos(angle)
    y = HEIGHT//2 + dist * math.sin(angle)
    speed = random.uniform(2, 5)
    vx = -speed * math.sin(angle)
    vy = speed * math.cos(angle)
    mass = random.uniform(3, 10)
    color = (150, 150, 150)
    asteroids.append(Body(x, y, vx, vy, mass, color, 5))

# Список всех объектов
bodies = [star, planet1, planet2, planet3] + asteroids

# Список частиц взрыва
explosion_particles = []

# Параметры отображения
show_trails = True
show_collisions = True
collision_counter = 0
font = pygame.font.Font(None, 24)
font_small = pygame.font.Font(None, 18)

# Переменные для перетаскивания
dragging_body = None
mouse_pressed = False
selected_body = None  # Выбранный объект

# Главный игровой цикл
running = True
paused = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                mouse_x, mouse_y = pygame.mouse.get_pos()
                mouse_pressed = True
                
                # Проверяем клик по объектам (сначала ищем под курсором)
                clicked_body = None
                for body in reversed(bodies):
                    if body.is_clicked(mouse_x, mouse_y) and not body.is_fixed:
                        clicked_body = body
                        break
                
                if clicked_body:
                    # Если кликнули по объекту - начинаем перетаскивание
                    clicked_body.start_drag(mouse_x, mouse_y)
                    dragging_body = clicked_body
                    # Снимаем выделение с других
                    for body in bodies:
                        if body != clicked_body:
                            body.is_selected = False
                    clicked_body.is_selected = True
                    selected_body = clicked_body
                else:
                    # Клик по пустому месту - снимаем выделение
                    for body in bodies:
                        body.is_selected = False
                    selected_body = None
                        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:  # Правая кнопка мыши - изменить скорость
                if selected_body and not selected_body.is_fixed:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Задаем новое направление скорости от объекта к курсору
                    dx = mouse_x - selected_body.x
                    dy = mouse_y - selected_body.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 10:
                        speed = math.sqrt(selected_body.vx**2 + selected_body.vy**2)
                        if speed < 0.1:
                            speed = 2
                        selected_body.vx = dx / dist * speed
                        selected_body.vy = dy / dist * speed
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
                if dragging_body:
                    dragging_body.stop_drag()
                    dragging_body = None
                    
        elif event.type == pygame.MOUSEMOTION:
            if dragging_body and mouse_pressed:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dragging_body.update_drag(mouse_x, mouse_y)
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_r:
                # Сброс всех объектов
                bodies.clear()
                explosion_particles.clear()
                dragging_body = None
                mouse_pressed = False
                selected_body = None
                
                star = Body(WIDTH//2, HEIGHT//2, vx=0, vy=0, mass=1000, color=YELLOW, radius=10, is_fixed=True)
                planet1 = Body(WIDTH//2 + 200, HEIGHT//2, vx=0, vy=3.2, mass=30, color=BLUE, radius=15)
                planet2 = Body(WIDTH//2 - 250, HEIGHT//2 + 50, vx=0, vy=-2.8, mass=25, color=GREEN, radius=12)
                planet3 = Body(WIDTH//2 + 100, HEIGHT//2 - 300, vx=4.5, vy=1.5, mass=15, color=RED, radius=10)
                asteroids = []
                for i in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(100, 350)
                    x = WIDTH//2 + dist * math.cos(angle)
                    y = HEIGHT//2 + dist * math.sin(angle)
                    speed = random.uniform(2, 5)
                    vx = -speed * math.sin(angle)
                    vy = speed * math.cos(angle)
                    mass = random.uniform(3, 10)
                    color = (150, 150, 150)
                    asteroids.append(Body(x, y, vx, vy, mass, color, 5))
                bodies = [star, planet1, planet2, planet3] + asteroids
                collision_counter = 0
            elif event.key == pygame.K_c:
                show_collisions = not show_collisions
            elif event.key == pygame.K_t:
                show_trails = not show_trails
            elif event.key == pygame.K_a:
                # Добавить случайный астероид
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(100, 350)
                x = WIDTH//2 + dist * math.cos(angle)
                y = HEIGHT//2 + dist * math.sin(angle)
                speed = random.uniform(2, 6)
                vx = -speed * math.sin(angle) + random.uniform(-1, 1)
                vy = speed * math.cos(angle) + random.uniform(-1, 1)
                mass = random.uniform(3, 10)
                bodies.append(Body(x, y, vx, vy, mass, (150, 150, 150), 5))
            elif event.key == pygame.K_m:
                # Создать новую планету в позиции мыши
                mouse_x, mouse_y = pygame.mouse.get_pos()
                mass = random.uniform(10, 50)
                color = random.choice([RED, BLUE, GREEN, ORANGE, PURPLE])
                new_planet = Body(mouse_x, mouse_y, vx=random.uniform(-2, 2), 
                                vy=random.uniform(-2, 2), mass=mass, color=color, radius=10)
                bodies.append(new_planet)
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                # Удалить выбранный объект
                if selected_body and not selected_body.is_fixed:
                    if selected_body in bodies:
                        bodies.remove(selected_body)
                    selected_body = None
            elif event.key == pygame.K_UP:
                # Увеличить скорость выбранного объекта
                if selected_body and not selected_body.is_fixed:
                    speed = math.sqrt(selected_body.vx**2 + selected_body.vy**2)
                    if speed > 0:
                        selected_body.vx *= 1.1
                        selected_body.vy *= 1.1
                    else:
                        selected_body.vx += 0.1
            elif event.key == pygame.K_DOWN:
                # Уменьшить скорость выбранного объекта
                if selected_body and not selected_body.is_fixed:
                    speed = math.sqrt(selected_body.vx**2 + selected_body.vy**2)
                    if speed > 0:
                        selected_body.vx *= 0.9
                        selected_body.vy *= 0.9

    if not paused:
        # Обновляем частицы взрыва
        for particle in explosion_particles[:]:
            particle.update()
            if not particle.alive:
                explosion_particles.remove(particle)
        
        # Рассчитываем орбитальные параметры для всех объектов относительно звезды
        for body in bodies:
            if body != star:
                body.calculate_orbit_params(star)
        
        # Применяем гравитацию для всех пар объектов
        for i, body1 in enumerate(bodies):
            if not body1.alive:
                continue
            for body2 in bodies[i+1:]:
                if not body2.alive:
                    continue
                body1.apply_gravity(body2)
                body2.apply_gravity(body1)
                
                # Проверяем столкновения
                if body1.check_collision(body2):
                    collision_counter += 1
        
        # Удаляем мертвые объекты
        bodies = [body for body in bodies if body.alive]
        
        # Обновляем позиции
        for body in bodies:
            body.update_position()
            
            # Обновляем следы
            if show_trails and not body.is_dragging:
                body.trail.append((body.x, body.y))
                if len(body.trail) > 30:
                    body.trail.pop(0)

    # --- Отрисовка ---
    screen.fill(BLACK)
    
    # Рисуем сетку
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (20, 20, 20), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (20, 20, 20), (0, y), (WIDTH, y))
    
    # Рисуем следы
    if show_trails:
        for body in bodies:
            if len(body.trail) > 1:
                for i in range(1, len(body.trail)):
                    size = max(1, int(body.get_radius() * 0.3 * i / len(body.trail)))
                    pygame.draw.circle(screen, body.color, 
                                     (int(body.trail[i][0]), int(body.trail[i][1])), 
                                     size)
    
    # Рисуем все объекты
    for body in bodies:
        body.draw(screen)
    
    # Рисуем частицы взрыва
    for particle in explosion_particles:
        particle.draw(screen)
    
    # Отображаем информацию о выбранном объекте
    if selected_body and selected_body != star:
        info_y = 10
        orbit_info = [
            f" Выбран: масса={int(selected_body.mass)}",
            f" Радиус орбиты: {int(selected_body.orbit_radius)}",
            f" Орб. скорость: {selected_body.orbit_speed:.2f}",
            f" Период: {selected_body.orbit_period:.1f}" if selected_body.orbit_period != float('inf') else "🔄 Период: бесконечный",
            f" Эксцентриситет: {selected_body.eccentricity:.3f}",
            f" Энергия: {selected_body.orbital_energy:.2f}",
            f"",
            f"Управление:",
            f"скорость",
            f"ПКМ - направить скорость",
            f"Delete - удалить"
        ]
        
        for i, text in enumerate(orbit_info):
            text_surface = font_small.render(text, True, CYAN)
            screen.blit(text_surface, (WIDTH - 250, info_y + i * 20))
    elif selected_body == star:
        info_y = 10
        star_info = [
            f" ЗВЕЗДА (фиксирована)",
            f"Масса: {int(star.mass)}",
            f"Объектов на орбите: {len(bodies)-1}"
        ]
        for i, text in enumerate(star_info):
            text_surface = font_small.render(text, True, YELLOW)
            screen.blit(text_surface, (WIDTH - 250, info_y + i * 20))
    
    # Информация на экране
    info = [
        f"Пробел - пауза | R - сброс | C - коллизии | T - следы | A - астероид | M - планета",
        f"Объектов: {len(bodies)} | Коллизий: {collision_counter} | Частиц: {len(explosion_particles)}",
        f"G = {G} | Упругость: {COLLISION_DAMPING}",
        f" Клик по объекту - выбрать | Перетащить - изменить орбиту",
        f"Выбран: {selected_body.color if selected_body else 'Нет'}"
    ]
    for i, text in enumerate(info):
        text_surface = font.render(text, True, WHITE)
        screen.blit(text_surface, (10, 10 + i * 25))
    
    # Отображаем статус коллизий
    if show_collisions and collision_counter > 0:
        col_text = font.render(f" ВЗРЫВ! {collision_counter}", True, RED)
        screen.blit(col_text, (WIDTH//2 - 100, 50))
    
    # Отображаем подсказку при перетаскивании
    if dragging_body:
        help_text = font.render("Перетаскивание... Отпустите кнопку мыши", True, LIGHT_BLUE)
        screen.blit(help_text, (WIDTH//2 - 150, HEIGHT - 50))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()