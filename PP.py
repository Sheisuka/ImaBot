# PICTURE PROCESSING


from PIL import Image, ImageDraw, ImageFont
import cv2
import time
import json
import os
import sys


def try_to_save(img: Image, user: str, form: str) -> Exception | None:
    try:
        img = img.save(f"data/photos/to_send/{user}.{form}")
    except IOError as error:
        return error
    return None


def rotate_image(user: str, degrees: int) -> Exception | None:
    img = Image.open(f"data/photos/get/{user}_photo.jpg")
    rotated_image = img.rotate(degrees, expand=True)
    return try_to_save(rotated_image, user, 'jpg')


def gray_scale(user: str) -> None | Exception:
    img = Image.open(f"data/photos/get/{user}_photo.jpg")
    gray_image = img.convert('L')
    return try_to_save(gray_image, user, 'jpg')


def check_count_pixels(image: str) -> int:
    size = Image.open(image).size
    return size[0] * size[1] < 600 ** 2


def count_unique(image: str, user: str) -> list:
    """ Подсчет пикселей, распределение по группам, отрисовка вывода"""

    # Подсчет пикселей и группировка
    with open('data/colors.json') as file:
        color_dict = json.load(file)
    image = Image.open(image)
    x, y = image.size
    q = 0
    pixels = image.load()
    unique_pixels = dict()
    for x_i in range(x):
        for y_i in range(y):
            r, g, b = pixels[x_i, y_i]
            q += 1
            for key, value in color_dict.items():
                if value[0] <= r and value[1] <= g and value[2] <= b:
                    if key in unique_pixels:
                        unique_pixels[key].append((x_i, y_i))
                        break
                    else:
                        unique_pixels[key] = [(x_i, y_i)]
                        break
    sorted_ = (sorted(unique_pixels.items(), key=lambda item: len(item[1]), reverse=True))[:48]

    # Создание изображения для вывода пользователю
    pixels_count, pixel_size = 20, 15
    font = ImageFont.truetype('data/fonts/tnr.ttf', size=13)
    pixels_pic = Image.new('RGB', (800, 500), 'white')
    draw = ImageDraw.Draw(pixels_pic)
    cord_x, cord_y = 30, 20
    for index, item in enumerate(sorted_):
        name = item[0]
        count = len(item[1])
        rgb_value = tuple(color_dict[name][0:3])
        draw.text((cord_x - pixel_size - 5, cord_y), text=str(index + 1), font=font, fill='black')
        draw.rectangle((cord_x, cord_y, cord_x + pixel_size, cord_y + pixel_size), fill=rgb_value)
        draw.line(((cord_x - 1, cord_y - 1), (cord_x + pixel_size + 1, cord_y - 1),
                   (cord_x + 1 + pixel_size, cord_y + 1 + pixel_size),
                   (cord_x - 1, cord_y + 1 + pixel_size), (cord_x - 1, cord_y - 1)), fill='black', width=1)
        draw.text((cord_x + pixel_size * 2, cord_y), text=f'{name}', font=font, fill='black')
        draw.text((cord_x + pixel_size * 10, cord_y), text=f'{count} pixels', font=font, fill='black')
        cord_y += 30
        if cord_y >= 500:
            cord_x, cord_y = cord_x + 265, 20
    try_to_save(pixels_pic, user, 'jpg')
    return sorted_


def alpha_image(positions: list, user: str) -> Exception | None:
    img = Image.open(f"data/photos/get/{user}_photo.jpg")
    pixels = img.load()
    img_new = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_new.show()
    img_new.paste(img)
    pixels_new = img_new.load()
    for pos in positions:
        x, y = pos
        pixels_new[x, y] = (0, 0, 0, 0)
    return try_to_save(img_new, user, 'png')


def to_png(user: str) -> Exception | None:
    path = f"data/photos/get/{user}_photo.jpg"
    new_path = path.split('.')[0] + 'png'
    img = Image.open(path)
    return try_to_save(img, new_path, 'png')


def change_color(positions: list, to: tuple, user: str) -> Exception | None:
    img = Image.open(f"data/photos/get/{user}_photo.jpg")
    pixels = img.load()
    for pos in positions:
        x, y = pos
        pixels[x, y] = to
    return try_to_save(img, user, 'jpg')


# def resize(image, percents):
#     image = cv2.imread(image, cv2.IMREAD_UNCHANGED)
#     if percents != 0:
#         width = int(image.shape[1] * percents / 100)
#         height = int(image.shape[0] * percents / 100)
#         dim = (width, height)
#         resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
#         cv2.imwrite()
#     else:
#         return 'Я не люблю когда надо мной так шутят'
