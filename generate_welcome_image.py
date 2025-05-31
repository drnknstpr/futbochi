from PIL import Image, ImageDraw, ImageFont
import os
from math import sin, cos, radians

def draw_diagonal_stripe(draw, x, y, width, height, angle, color, stripe_width=100):
    """Рисует диагональную полосу заданного цвета"""
    points = [
        (x, y),
        (x + stripe_width * cos(radians(angle)), y - stripe_width * sin(radians(angle))),
        (x + width * cos(radians(angle)) + stripe_width * cos(radians(angle)), 
         y + width * sin(radians(angle)) - stripe_width * sin(radians(angle))),
        (x + width * cos(radians(angle)), y + width * sin(radians(angle)))
    ]
    draw.polygon(points, fill=color)

# Создаем изображение
width = 1200
height = 1500  # Увеличиваем высоту для лучшей композиции
image = Image.new('RGB', (width, height), color='#0B1741')  # Темно-синий фон

# Получаем объект для рисования
draw = ImageDraw.Draw(image)

# Рисуем диагональные полосы
stripes = [
    {'angle': -30, 'color': '#E31B23', 'offset': 200},  # Красный
    {'angle': -35, 'color': '#1DB954', 'offset': 400},  # Зеленый
    {'angle': -25, 'color': '#6A0DAD', 'offset': 600},  # Фиолетовый
    {'angle': -40, 'color': '#E31B23', 'offset': 800},  # Красный
    {'angle': -20, 'color': '#1DB954', 'offset': 1000}  # Зеленый
]

for stripe in stripes:
    draw_diagonal_stripe(
        draw,
        -200 + stripe['offset'],
        0,
        width + 400,
        height,
        stripe['angle'],
        stripe['color'],
        200
    )

# Загружаем шрифт (используем системный шрифт, если специальный не установлен)
try:
    title_font = ImageFont.truetype("Arial Bold.ttf", 250)
    subtitle_font = ImageFont.truetype("Arial.ttf", 120)
except:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

# Добавляем текст "FUT"
fut_text = "FUT"
fut_bbox = draw.textbbox((0, 0), fut_text, font=title_font)
fut_width = fut_bbox[2] - fut_bbox[0]
fut_x = (width - fut_width) // 2
draw.text((fut_x, 100), fut_text, font=title_font, fill='#F5F5F5')

# Добавляем текст "BO"
bo_text = "BO"
bo_bbox = draw.textbbox((0, 0), bo_text, font=title_font)
bo_width = bo_bbox[2] - bo_bbox[0]
bo_x = (width - bo_width) // 2
draw.text((bo_x, 300), bo_text, font=title_font, fill='#F5F5F5')

# Добавляем текст "CHI"
chi_text = "CHI"
chi_bbox = draw.textbbox((0, 0), chi_text, font=title_font)
chi_width = chi_bbox[2] - chi_bbox[0]
chi_x = (width - chi_width) // 2
draw.text((chi_x, 500), chi_text, font=title_font, fill='#F5F5F5')

# Добавляем логотип SirenaBet
logo_text = "SIRENABET"
logo_bbox = draw.textbbox((0, 0), logo_text, font=subtitle_font)
logo_width = logo_bbox[2] - logo_bbox[0]
logo_x = (width - logo_width) // 2
draw.text((logo_x, height - 300), logo_text, font=subtitle_font, fill='#FFD700')

# Добавляем призыв к действию
cta_text = "СОБЕРИ ТОП-КОМАНДУ!"
cta_bbox = draw.textbbox((0, 0), cta_text, font=subtitle_font)
cta_width = cta_bbox[2] - cta_bbox[0]
cta_x = (width - cta_width) // 2
draw.text((cta_x, height - 150), cta_text, font=subtitle_font, fill='#F5F5F5')

# Создаем директорию media, если её нет
os.makedirs('media', exist_ok=True)

# Сохраняем изображение
image.save('media/welcome.png') 