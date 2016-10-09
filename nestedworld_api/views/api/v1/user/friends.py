from flask import jsonify, request
from marshmallow import post_dump
from nestedworld_api.app import ma
from nestedworld_api.login import login_required, current_session
from . import users

user_friend = users.namespace('friends')


@user_friend.route('/')
class UserFriend(user_friend.Resource):
    tags = ['users']

    class FriendResult(ma.Schema):

        # TODO : Maybe use the User.Schema ?
        class User(ma.Schema):
            pseudo = ma.String()
            birth_date = ma.Date()
            city = ma.String()
            gender = ma.String()
            avatar = ma.Url()
            background = ma.Url()
            registered_at = ma.DateTime(dump_only=True)
            level = ma.Integer()
            is_connected = ma.Boolean()

        user = ma.Nested(User, attribute='friend')

        @post_dump(pass_many=True)
        def add_envelope(self, data, many):
            namespace = 'friends' if many else 'friend'
            return {namespace: data}

    class FriendRequest(ma.Schema):

        pseudo = ma.String()

    @login_required
    @user_friend.marshal_with(FriendResult(many=True))
    def get(self):
        '''
            Retrieve current user's friends list.

            This request is used by a user for retrieve his own friends list.
        '''
        from nestedworld_api.db import UserFriend

        friends = UserFriend.query\
                            .filter(UserFriend.user_id == current_session.user.id)\
                            .all()
        return friends

    @login_required
    @user_friend.accept(FriendRequest())
    @user_friend.marshal_with(FriendResult())
    def post(self, data):
        '''
            Add an user in to current user's friends list

            This request is used by a user for create a link between him
            and another existing user as friend.
        '''
        from nestedworld_api.db import db
        from nestedworld_api.db import User, UserFriend

        friend = User.query.filter(
            User.pseudo == data['pseudo']).first()
        if friend is None:
            user_friend.abort(400, message='Friend not found')

        friends_count = UserFriend.query\
                                  .filter((UserFriend.user_id == current_session.user.id) &
                                          (UserFriend.friend_id == friend.id))\
                                  .count()
        if friends_count > 0:
            user_friend.abort(400, message='Friend already added')

        result = UserFriend(user=current_session.user, friend=friend)
        db.session.add(result)
        db.session.commit()

        return result
