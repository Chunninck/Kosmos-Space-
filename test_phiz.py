if True:
    import pygame
    import math

    # Инициализация
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Движение по окружности")
    clock = pygame.time.Clock()

    # Параметры орбиты
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    radius = 150          # Радиус окружности
    angle = 0             # Текущий угол (в радианах)
    speed = 0.02          # Скорость вращения (чем больше, тем быстрее)

    # Цвета
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLACK = (0, 0, 0)

    # Главный игровой цикл
    running = True
    while running:
        # Обработка выхода из игры
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Логика движения ---
        # 1. Вычисляем новые координаты
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # 2. Увеличиваем угол для следующего кадра
        angle += speed

        # --- Отрисовка ---
        screen.fill(BLACK)  # Заливаем фон
        
        # Рисуем белую траекторию (круг)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), radius, 1)
        
        # Рисуем центр (маленькая белая точка)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), 5)
        
        # Рисуем наш движущийся объект (красный шарик)
        pygame.draw.circle(screen, RED, (int(x), int(y)), 20)

        # Обновляем экран
        pygame.display.flip()
        
        # Ограничиваем FPS (60 кадров в секунду)
        clock.tick(60)