import vk_api
from vk_api.exceptions import ApiError
from config import VKConfig
import sys


class VKFinder:

    def __init__(self, login=None, password=None):
        if login and password:
            self.api = self.__auth(login, password)
        else:
            self.api = self.__auth(VKConfig.login, VKConfig.password)

    def __auth(self, login, password):
        try:
            session = vk_api.VkApi(login, password)
            session.auth()
            return session.get_api()
        except Exception as e:
            print('Cannot auth with creds. Failed with error')
            print(e)
            sys.exit(0)

    def chunked_getter(self, step, other: bool, **kwargs):
        offset = 0
        other_fields = {'profiles': [], 'groups': []}
        step = step
        result = []
        max_count = 1
        while len(result) != max_count:
            kwargs['values'].update({'count': step, 'offset': offset})
            try:
                res = self.api._vk.method(**kwargs)
            except ApiError as e:
                print('ERROR: ', e)
                return result, False
            max_count = res.get('count')
            offset += step
            if other:
                for key, value in other_fields.items():
                    value += res.get(key)
            result += res.get('items')
            if offset > len(result) + step:
                break
        return result, other_fields

    def get_profile_friends(self,  user_id):
        step = 5000
        params = dict(method='friends.get', values={'user_id': user_id, 'fields': 'sex'})
        result, _ = self.chunked_getter(step, False, **params)
        return result

    def get_profile_photos(self, profile_id):
        step = 200
        params = dict(method='photos.getAll', values={'owner_id': profile_id, 'extended': 1})
        result, _ = self.chunked_getter(step, False, **params)
        for i in result:
            if i.get('sizes'):
                sizes = [j.get('width') for j in i.get('sizes')]
                index_max_size = sizes.index(max(sizes))
                i['url'] = i.get('sizes')[index_max_size].get('url')
                i.pop('sizes')
        return result

    def get_photos_by_id(self, ids: list):
        if not isinstance(ids, list):
            ids = [ids]
        params = dict(method='photos.getById', values={'photos': ','.join([str(i) for i in ids])})
        try:
            result = self.api._vk.method(**params)
        except ApiError as e:
            print("ERROR: ", e)
            return []
        for i in result:
            if i.get('sizes'):
                sizes = [j.get('width') for j in i.get('sizes')]
                index_max_size = sizes.index(max(sizes))
                i['url'] = i.get('sizes')[index_max_size].get('url')
                i.pop('sizes')
        return result
