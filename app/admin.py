from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import flash
from werkzeug.security import generate_password_hash

from app import app, db
from app.models import User


class UserModelView(ModelView):
    can_delete = False
    can_create = True
    can_edit = True

    column_list = ['id', 'username', 'used_storage', 'storage_limit', 'is_locked']
    form_edit_rules = ('storage_limit',)
    form_create_rules = ('username', 'storage_limit')
    form_excluded_columns = ['password', 'used_storage']

    def on_model_change(self, form, model, is_created):
        from werkzeug.security import generate_password_hash
        if is_created:
            model.password = generate_password_hash("1234")
            if model.storage_limit is None:
                model.storage_limit = 1024.00
        else:
            if model.storage_limit is None:
                model.storage_limit = 1024.00
            if model.used_storage > model.storage_limit:
                raise ValueError("Storage limit cannot be less than used storage.")
        return super().on_model_change(form, model, is_created)

    @action('reset_password', 'Reset Password', 'Reset selected users password to "1234"?')
    def action_reset_password(self, ids):
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            user.password = generate_password_hash("1234")
        db.session.commit()

    @action('lock_user', 'Lock user', 'Confirm to lock selected users?')
    def action_lock_user(self, ids):
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            user.is_locked = True
        db.session.commit()

    @action('unlock_user', 'Unlock user', 'Confirm to unlock selected users?')
    def action_unlock_user(self, ids):
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            user.is_locked = False
        db.session.commit()

admin = Admin(app, name='Admin Panel', template_mode='bootstrap4')
admin.add_view(UserModelView(User, db.session))
