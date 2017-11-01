import os

class View(object):
    def __new__(cls, *args, **kwargs):
        pass

    def get(self):
        '''
        RESTful get method
        :return:
        '''
        raise NotImplementedError

    def post(self):
        '''
        RESTful get method
        :return:
        '''
        raise NotImplementedError

    def put(self):
        '''
        RESTful get method
        :return:
        '''
        raise NotImplementedError

    def delete(self):
        '''
        RESTful get method
        :return:
        '''
        raise NotImplementedError

    def option(self):
        '''
        RESTful get method
        :return:
        '''
        raise NotImplementedError

    pass