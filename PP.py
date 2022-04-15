# PICTURE PROCESSING


from PIL import Image
from pprint import pprint as print
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


def gray_scale(image: str):
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


def count_unique(image: str) -> dict:
    image = Image.open(image)
    x, y = image.size
    pixels = image.load()
    unique_pixels = dict()
    for x_i in range(x):
        for y_i in range(y):
            if pixels[x_i, y_i] in unique_pixels:
                unique_pixels[pixels[x_i, y_i]] += 1
            else:
                unique_pixels[pixels[x_i, y_i]] = 1
    sorted_ = sorted(unique_pixels.items(), key=lambda item: item[1], reverse=True)
    sorted_unique = {k: v for k, v in sorted_}
    return sorted_unique



def alpha_image(image: str, pixel):



def jpg_to_png(image: str):
    try:
        new_image = image.split('.')[0] + '.png'
        Image.open(image).save(new_image)
        return new_image
    except IOError as error:
        return error


def change_color(what, to):
    pass


def delete_color(num):
    pass


def resize(image):
    pass


def crop_photo(image):
    pass

print(count_unique('data/photos/sheisuka_photo.jpg'))