import pygame
import math
import sys

# Инициализация
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Космическая гравитация")
clock = pygame.time.Clock()

# Константы
G = 6.67  # Гравитационная постоянная (чем больше, тем сильнее притяжение)

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

class Body:
    def __init__(self, x, y, vx=0, vy=0, mass=50, color=RED, radius=20):
        self.x = x
        self.y = y
        self.vx = vx  # скорость по X
        self.vy = vy  # скорость по Y
        self.mass = mass  # масса объекта
        self.color = color
        self.radius = radius  # визуальный размер (зависит от массы)
        
    def update_position(self):
        """Обновление позиции на основе скорости"""
        self.x += self.vx
        self.y += self.vy
        
    def apply_gravity(self, other):
        """Применение гравитации от другого объекта"""
        # Вычисляем расстояние между объектами
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Избегаем деления на ноль
        if distance < 1:
            distance = 1
            
        # Вычисляем силу гравитации (F = G * M * m / r^2)
        force = G * self.mass * other.mass / (distance ** 2)
        
        # Направление силы (единичный вектор)
        fx = dx / distance
        fy = dy / distance
        
        # Ускорение (F = m * a => a = F / m)
        # Ускорение действует на текущий объект от другого
        ax = force * fx / self.mass
        ay = force * fy / self.mass
        
        # Изменяем скорость
        self.vx += ax
        self.vy += ay
        
    def get_radius(self):
        """Возвращает визуальный радиус в зависимости от массы"""
        # Радиус пропорционален кубическому корню из массы
        return max(5, self.radius * (self.mass ** (1/3)) / 3.7)
        
    def draw(self, screen):
        """Отрисовка объекта"""
        rad = self.get_radius()
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(rad))
        
        # Отображаем массу
        font = pygame.font.Font(None, 20)
        mass_text = font.render(f"M={int(self.mass)}", True, WHITE)
        screen.blit(mass_text, (self.x - 20, self.y - rad - 20))

# Создаем объекты
# Центральный объект (звезда) - большая масса, неподвижный
star = Body(WIDTH//2, HEIGHT//2, vx=0, vy=0, mass=300, color=YELLOW, radius=20)

# Планета 1 - движется по орбите
planet1 = Body(
    WIDTH//2 + 200, 
    HEIGHT//2, 
    vx=0, 
    vy=3,  # начальная скорость для круговой орбиты
    mass=20, 
    color=BLUE, 
    radius=15
)

# Планета 2 - движется по другой орбите
planet2 = Body(
    WIDTH//2 - 250, 
    HEIGHT//2 + 50, 
    vx=0, 
    vy=-2.5, 
    mass=25, 
    color=GREEN, 
    radius=12
)

# Планета 3 - маленький объект
planet3 = Body(
    WIDTH//2 + 100, 
    HEIGHT//2 - 300, 
    vx=4.5, 
    vy=1, 
    mass=15, 
    color=RED, 
    radius=10
)

# Список всех объектов
bodies = [star, planet1, planet2, planet3]

# Параметры отображения
show_velocities = True  # Показывать ли векторы скорости
show_trails = True  # Показывать ли следы
trails = {body: [] for body in bodies}  # Следы движения
MAX_TRAIL_LENGTH = 50  # Максимальная длина следа

# Главный игровой цикл
running = True
paused = False
while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  # Пауза по пробелу
                paused = not paused
            elif event.key == pygame.K_r:  # Сброс по R
                # Возвращаем объекты на начальные позиции
                star.x, star.y = WIDTH//2, HEIGHT//2
                star.vx, star.vy = 0, 0
                star.mass = 200
                
                planet1.x, planet1.y = WIDTH//2 + 200, HEIGHT//2
                planet1.vx, planet1.vy = 0, 3
                planet1.mass = 30
                
                planet2.x, planet2.y = WIDTH//2 - 250, HEIGHT//2 + 50
                planet2.vx, planet2.vy = 0, -2.5
                planet2.mass = 25
                
                planet3.x, planet3.y = WIDTH//2 + 100, HEIGHT//2 - 300
                planet3.vx, planet3.vy = 4.5, 1
                planet3.mass = 15
                
                trails = {body: [] for body in bodies}

    if not paused:
        # --- Логика гравитации ---
        # Для каждой пары объектов применяем гравитацию
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i+1:]:
                body1.apply_gravity(body2)
                body2.apply_gravity(body1)  # Третий закон Ньютона
                
        # Обновляем позиции всех объектов
        for body in bodies:
            body.update_position()
            
            # Обновляем следы
            if show_trails:
                trails[body].append((body.x, body.y))
                if len(trails[body]) > MAX_TRAIL_LENGTH:
                    trails[body].pop(0)

    # --- Отрисовка ---
    screen.fill(BLACK)
    
    # Рисуем сетку (для наглядности)
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (20, 20, 20), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (20, 20, 20), (0, y), (WIDTH, y))
    
    # Рисуем следы
    if show_trails:
        for body, trail in trails.items():
            if len(trail) > 1:
                # Градиентная прозрачность для следа
                for i in range(1, len(trail)):
                    alpha = int(255 * i / len(trail))
                    color = body.color[:3] + (alpha,) if len(body.color) == 4 else body.color
                    # Упрощенная отрисовка следа
                    pygame.draw.circle(screen, body.color, 
                                     (int(trail[i][0]), int(trail[i][1])), 
                                     max(1, int(body.get_radius() * i / len(trail))))
    
    # Рисуем все объекты
    for body in bodies:
        body.draw(screen)
    
    # Рисуем векторы скорости
    if show_velocities:
        for body in bodies:
            speed = math.sqrt(body.vx**2 + body.vy**2)
            if speed > 0.1:  # Рисуем только если есть скорость
                end_x = body.x + body.vx * 5
                end_y = body.y + body.vy * 5
                pygame.draw.line(screen, WHITE, (body.x, body.y), (end_x, end_y), 2)
                # Стрелка
                angle = math.atan2(body.vy, body.vx)
                arrow_length = 10
                pygame.draw.line(screen, WHITE, 
                               (end_x, end_y),
                               (end_x - arrow_length * math.cos(angle - 0.5),
                                end_y - arrow_length * math.sin(angle - 0.5)), 2)
                pygame.draw.line(screen, WHITE,
                               (end_x, end_y),
                               (end_x - arrow_length * math.cos(angle + 0.5),
                                end_y - arrow_length * math.sin(angle + 0.5)), 2)

    # Отображаем информацию
    font = pygame.font.Font(None, 24)
    info = [
        f"Пробел - пауза | R - сброс",
        f"G = {G} (гравитационная постоянная)",
        f"Всего объектов: {len(bodies)}",
    ]
    for i, text in enumerate(info):
        text_surface = font.render(text, True, WHITE)
        screen.blit(text_surface, (10, 10 + i * 25))
    
    # Обновляем экран
    pygame.display.flip()
    
    # Ограничиваем FPS
    clock.tick(60)

pygame.quit()
sys.exit()