from PIL import Image
import os


def try_to_save(img: Image, user: str, form: str) -> Exception | None:
    """ Сохряняет фото с указанными параметрами"""
    try:
        img.save(get_path(user, 'to_send', form))
    except IOError as error:
        return error
    return None


def get_path(user: str, direction: str, form: str) -> str:
    """ Возвращает путь до фотографии"""
    path = f'data/photos/{direction}/{user}.{form}'
    return path


def clear_directions(user: str):
    """ Удаляет все фото пользователя"""
    for folder in os.listdir('data/photos'):
        for file in os.listdir(f'data/photos/{folder}'):
            if user in file:
                os.remove(f'data/photos/{folder}/{file}')


