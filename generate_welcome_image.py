from PIL import Image, ImageDraw, ImageFont
import os

# Создаем изображение
width = 1200
height = 630
image = Image.new('RGB', (width, height), color='#1a1a2e')

# Получаем объект для рисования
draw = ImageDraw.Draw(image)

# Загружаем шрифт (используем системный шрифт, если специальный не установлен)
try:
    title_font = ImageFont.truetype("Arial Bold.ttf", 120)
    subtitle_font = ImageFont.truetype("Arial.ttf", 60)
except:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

# Добавляем градиентный фон
for y in range(height):
    r = int(26 + (y / height) * 20)
    g = int(26 + (y / height) * 20)
    b = int(46 + (y / height) * 30)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# Рисуем футбольный мяч (упрощенно)
ball_center = (width // 2, height // 2)
ball_radius = 100
draw.ellipse([
    ball_center[0] - ball_radius,
    ball_center[1] - ball_radius,
    ball_center[0] + ball_radius,
    ball_center[1] + ball_radius
], fill='white', outline='black', width=3)

# Добавляем пятиугольники на мяч
for i in range(5):
    x = ball_center[0] + int(ball_radius * 0.6 * (i / 5))
    y = ball_center[1] + int(ball_radius * 0.6 * (i / 5))
    draw.regular_polygon((x, y, 20), 5, rotation=30, fill='black')

# Добавляем заголовок
title_text = "FUTBOCHI"
title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = title_bbox[2] - title_bbox[0]
title_x = (width - title_width) // 2
draw.text((title_x, 100), title_text, font=title_font, fill='white')

# Добавляем логотип SirenaBet
logo_text = "SirenaBet"
logo_bbox = draw.textbbox((0, 0), logo_text, font=subtitle_font)
logo_width = logo_bbox[2] - logo_bbox[0]
logo_x = (width - logo_width) // 2
draw.text((logo_x, height - 200), logo_text, font=subtitle_font, fill='#ffd700')

# Добавляем призыв к действию
cta_text = "Собери топ-команду!"
cta_bbox = draw.textbbox((0, 0), cta_text, font=subtitle_font)
cta_width = cta_bbox[2] - cta_bbox[0]
cta_x = (width - cta_width) // 2
draw.text((cta_x, height - 100), cta_text, font=subtitle_font, fill='white')

# Создаем директорию media, если её нет
os.makedirs('media', exist_ok=True)

# Сохраняем изображение
image.save('media/welcome.png') 