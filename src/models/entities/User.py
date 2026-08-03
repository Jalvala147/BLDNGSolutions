from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, id, username, password, fullname="", tipoUsuario=0, areaUsuario=0) -> None:
        self.id = id
        self.username = username
        self.password = password
        self.fullname = fullname
        self.tipoUsuario = tipoUsuario
        self.areaUsuario = areaUsuario

    @classmethod
    def check_password(cls, hashed_password, password):
        from utils.passwords import check_password_hash
        return check_password_hash(hashed_password, password)
