# PICTURE PROCESSING


from PIL import Image
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


def count_pixels(image: str) -> int:
    size = Image.open(image).size
    return size[0] * size[1]


def alpha_image(image: str):
    pass


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

