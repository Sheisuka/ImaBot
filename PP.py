# PICTURE PROCESSING


from PIL import Image, ImageDraw, ImageFont
import cv2
import time
import json
import os
import sys


def rotate_image(image: str, degrees: int):
    try:
        image_name = Image.open(image)
        rotated_image = image_name.rotate(degrees, expand=True)
        rotated_image.save(image)
    except IOError as error:
        return error
    return


def gray_scale(image: str) -> None | Exception:
    try:
        image = Image.open(image)
        gray_image = image.convert('L')
        gray_image.save(image)
    except IOError as error:
        return error
    return


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
    pixels_pic = Image.new('RGB', (750, 550), 'white')
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
    pixels_pic.save(f'data/photos/to_send/{user}.jpg')
    return sorted_


def alpha_image(image: str, pixel):
    pass


def to_png(image: str):
    try:
        new_image = image.split('.')[0] + '.png'
        Image.open(image).save(new_image)
        return new_image
    except IOError as error:
        return error


def change_color(what, to):
    pass


def delete_color(image_name: str, num: int):
    image = Image.open(image_name, mode='RGBA')
    x, y = image.size
    pixels = image.load()
    for x_i in range(x):
        for y_i in range(y):
            if pixels[x_i, y_i] == num:
                pixels[x_i, y_i] = (0, 0, 0, 0)
    try:
        image.save(image_name)
    except IOError as error:
        return error


def resize(image, percents):
    image = cv2.imread(image, cv2.IMREAD_UNCHANGED)
    if percents != 0:
        width = int(image.shape[1] * percents / 100)
        height = int(image.shape[0] * percents / 100)
        dim = (width, height)
        resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
        # cv2.imwrite()
    else:
        return 'Я не люблю когда надо мной так шутят'
