from fastapi import HTTPException, status


class UserInactiveException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail='User is inactive')


class FileNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail='File not found')


class ValidationException(HTTPException):
    def __init__(self, item):
        self.item = item
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid {item}')
