# PICTURE PROCESSING


from PIL import Image, ImageDraw, ImageFont
import cv2
import json
import utility as ut


def rotate_image(user: str, degrees: int) -> Exception | None:
    """  Поворачивает изображение на указанную градусную меру против часовой стрелки"""
    img = Image.open(ut.get_path(user, 'get', 'jpg'))
    rotated_image = img.rotate(degrees, expand=True)
    return ut.try_to_save(rotated_image, user, 'jpg')


def black_and_white(user: str) -> None | Exception:
    im = Image.open(ut.get_path(user, 'get', 'jpg'))
    pixels = im.load()
    x, y = im.size
    for x_i in range(x):
        for y_i in range(y):
            r, g, b = pixels[x_i, y_i]
            average_rgb = int((r + g + b) / 3)
            if average_rgb < 126:
                pixels[x_i, y_i] = (0, 0, 0)
            else:
                pixels[x_i, y_i] = (255, 255, 255)
    return ut.try_to_save(im, user, 'jpg')


def gray_scale(user: str) -> None | Exception:
    im = Image.open(ut.get_path(user, 'get', 'jpg'))
    pixels = im.load()
    x, y = im.size
    for x_i in range(x):
        for y_i in range(y):
            r, g, b = pixels[x_i, y_i]
            average_rgb = int((0.3 * r) + (0.59 * g) + (0.11 * b))
            pixels[x_i, y_i] = (average_rgb, average_rgb, average_rgb)
    return ut.try_to_save(im, user, 'jpg')


def check_count_pixels(user: str) -> int:
    size = Image.open(ut.get_path(user, 'get', 'jpg')).size
    return size[0] * size[1] <= 1000 ** 2


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
    width = round(len(sorted_) / 16) * 266
    pixels_pic = Image.new('RGB', (width, 500), 'white')
    font = ImageFont.truetype('data/fonts/tnr.ttf', size=13)
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
    ut.try_to_save(pixels_pic, user, 'jpg')
    return sorted_


def alpha_image(positions: list, user: str) -> Exception | None:
    """ Делает пиксели по координатам из positions прозрачными. Результат сохраняет"""
    img = Image.open(ut.get_path(user, 'get', 'jpg'))
    img_new = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_new.show()
    img_new.paste(img)
    pixels_new = img_new.load()
    for pos in positions:
        x, y = pos
        pixels_new[x, y] = (0, 0, 0, 0)
    return ut.try_to_save(img_new, user, 'png')


def to_png(user: str) -> Exception | None:
    """ Меняет формат изображения на png"""
    path = f"data/photos/get/{user}.jpg"
    new_path = path.split('.')[0] + 'png'
    img = Image.open(path)
    return ut.try_to_save(img, new_path, 'png')


def change_color(positions: list, to: tuple, user: str) -> Exception | None:
    """ Меняет все пиксели по координатам из positions на пиксели со значением to. Результат сохраняет"""
    img = Image.open(ut.get_path(user, 'get', 'jpg'))
    pixels = img.load()
    for pos in positions:
        x, y = pos
        pixels[x, y] = to
    return ut.try_to_save(img, user, 'jpg')


def change_filepaths(user: str) -> Exception | list:
    """ Меняет местами фото для отправки и фото полученное с целью продолжения работы"""
    img_send = Image.open(ut.get_path(user, 'to_send', 'jpg'))
    try:
        img_send.save(ut.get_path(user, 'get', 'jpg'))
    except IOError as error:
        print(error.__class__.__name__)
    return count_unique(ut.get_path(user, 'get', 'jpg'), user)


def resize(user: str, percents: int):
    """ Изменяет размер фотографии на (percents + 100) процентов. Результат сохраняет"""
    image = cv2.imread(ut.get_path(user, 'get', 'jpg'), cv2.IMREAD_UNCHANGED)
    if percents in range(-99, 501):
        percents += 100
        width = int(image.shape[1] * percents / 100)
        height = int(image.shape[0] * percents / 100)
        dim = (width, height)
        resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
        try:
            cv2.imwrite(ut.get_path(user, 'to_send', 'jpg'), resized)
        except IOError as error:
            return error
        return None
    else:
        return 'Я не люблю когда надо мной так шутят'

