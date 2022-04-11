# PICTURE PROCESSING


from PIL import Image


def rotate_image(image, degrees):
    try:
        image = Image.open(image)
    except IOError:
        pass
    rotated_image = image.rotate(degrees)
    return rotated_image


def gray_scale(image):
    try:
        image = Image.open(image)
    except IOError:
        pass
    gray_image = image.convert('L')
    return gray_image


def alpha_image(image):
    pass
