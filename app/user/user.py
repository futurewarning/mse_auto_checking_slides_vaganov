from flask_login import logout_user, current_user

from app.bd_helper.bd_helper import add_user, validate_user, edit_user, delete_user, get_user, get_presentation, \
    get_check


def login(args):
    return validate_user(args['username'], args['password_hash'])


def signup(args):
    user = add_user(args['username'], args['password_hash'])
    if user is not None:
        user.name = args['name']
        if edit_user(user):
            return user
    return None


def logout():
    logout_user()
    return 'OK'


def signout():
    delete_user(current_user.username)
    logout_user()
    return 'OK'


def edit(json):
    current_user.name = json['name']
    return 'OK' if edit_user(current_user) else 'Not OK'


def get_rich(username):
    u = get_user(username)
    for i in range(0, len(u.presentations)):
        u.presentations[i] = get_presentation(u.presentations[i]._id)
        for j in range(0, len(u.presentations[i].checks)):
            u.presentations[i].checks[j] = get_check(u.presentations[i].checks[j]._id)
    return u
