'''
Created on Jul 10, 2017

@author: riccardo
'''
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    email = Column(String(150), unique=True)
    password = Column(String(150), nullable=True)  # not used for the moment
    permission_regex = Column(String(500), nullable=False)

    @property
    def asgitauthor(self):
        '''returns the string used to identify this user as git author'''
        frmt = "{name} <{email}>"
        name = self.name
        if not name:
            idx = self.email.find('@')
            if idx == -1:
                idx = None
            name = self.email[None:idx]

        return frmt.format(name=name, email=self.email)

    # mandatory flask-login properties:
    # See:
    # https://github.com/maxcountryman/flask-login/blob/master/docs/index.rst#your-user-class
    # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
    @property
    def is_authenticated(self):
        '''In general this method should just return True unless the object represents
        a user that should not be allowed to authenticate for some reason.'''
        return True

    @property
    def is_active(self):
        '''This property should return True for users unless they are inactive,
        for example because they have been banned.'''
        return True

    @property
    def is_anonymous(self):
        '''This property should return True only for fake users that are
        not supposed to log in to the system.'''
        return False

    def get_id(self):
        '''method should return a unique identifier for the user, in unicode format.
        We use the unique id generated by the database layer for this'''
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User email=%r>' % (self.email)
