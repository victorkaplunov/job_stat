import os
import yaml


def config_dict():
    """ Читает yaml-файл и возвращает словарь с параметрами тестов,
    а в случае неудачи - печатает сообщение об ошибке."""
    with open(str(os.path.dirname(__file__)) + '/' + "config.yaml", 'rt', encoding='utf8') as stream:
        try:
            return yaml.safe_load(stream)
        except KeyError:
            return print("Параметр не найден в config.yaml.", KeyError)
        except yaml.YAMLError as exc:
            return print(exc)


class ConfigObj:
    LOCAL_HOST_BASE_URL = config_dict()['local_host_base_url']
