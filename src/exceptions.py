from fastapi import HTTPException


class UserInactiveException(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail='User is inactive')


class FileNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail='File not found')


class ValidationException(HTTPException):
    def __init__(self, item):
        self.item = item
        super().__init__(status_code=400, detail=f'Invalid {item}')
