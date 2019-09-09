# -*- coding: utf-8 -*-

class Settings:
    """ Hack class for the resolve old UserProfile 
    (custom user model) db model dependency (old migrations files), 
    before create the new Profile (custom user model)"""
    AUTH_USER_MODEL = 'aklub.UserProfile'
