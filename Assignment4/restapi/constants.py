from enum import Enum

class Modelsconstants(Enum):
    MAX_LENGTH1 = '200',
    MAX_LENGTH2 = '100',
    MAX_DIGITS = '10',
    DECIMAL_PLACES = '2',
    FOREIGN_KEY_DEFAULT = '1'

class APIConstants(Enum):
    POST = 'POST',
    GET = 'GET',
    DELETE = 'DELETE',
    PUT = 'PUT',

class ActionConstants(Enum):
    POST = 'post',
    GET = 'get',
    DELETE = 'delete'
    PUT = 'put'

FILE_READER_TIMEOUT = 60