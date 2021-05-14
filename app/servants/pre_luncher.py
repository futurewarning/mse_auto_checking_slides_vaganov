from pymongo.errors import ConnectionFailure

from app.bd_helper.bd_helper import add_user, get_user, get_client, edit_user


def __js_hash(password):
    password_hash = 0
    if len(password) == 0:
        return password_hash
    for char in password:
        password_hash = ((password_hash << 5) - password_hash) + ord(char)
        password_hash = password_hash & password_hash
    return password_hash


def init(debug):
    try:
        get_client().admin.command('ismaster')
        print("MongoDB работает!")
    except ConnectionFailure:
        print("MongoDB не доступна!")
        return False

    if not debug:
        print("Удачного запуска!")
        return True

    cred = "admin"
    user = get_user(cred)
    if user is None:
        user = add_user(cred, __js_hash(cred))
        user.name = cred
        user.is_admin = True
        edit_user(user)

    print("Создан пользователь по умолчанию: { логин: " + user.username + ", пароль: " + cred + " }")

    return True
