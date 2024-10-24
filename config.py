import os
from pathlib import Path

# basedir = os.path.abspath(os.path.dirname(__file__))
from flask import request


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or "supersupersupersecretkey"
    # Genera la chiave di sessione utilizzando l'indirizzo IP dell'utente

    @staticmethod
    def init_app(app):
        pass



class ProdConfig(Config):
    pass


class DevConfig(Config):
    #SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(secretsData.dbUser, secretsData.dbPass,secretsData.dbHost, secretsData.dbPort,secretsData.dbSchema)
    DEBUG = True



class TestConfig(Config):

    # SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "testdata.sqlite")

    # To test configuration usage in unit test
    TESTING = True
    # disabling CSRF protection in the testing configuration
    WTF_CSRF_ENABLED = False
    # test admin
    EMAIL_ADMIN = "test1@test.it"


config = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': DevConfig
}
