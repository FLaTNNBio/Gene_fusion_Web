from flask import Flask
from flask_bootstrap import Bootstrap
from flask_uploads import UploadSet, IMAGES
from flask_cors import CORS

from config import config


# Use bootstrap with the app
bootstrap = Bootstrap()
images = UploadSet('images', IMAGES)


def create_app(config_name):

    app = Flask(__name__, static_folder="static")
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    CORS(app)  # Abilita CORS per tutta l'applicazione
    bootstrap.init_app(app)

    from gene_fusion_webApp.main.routes import main_blueprint
    from gene_fusion_webApp.datasets_generation.routes import dataset_generation_blueprint
    from gene_fusion_webApp.Training_Model.routes import training_blueprint
    from gene_fusion_webApp.combinatorics_methods.routes import combinatorics_method_blueprint

    app.register_blueprint(main_blueprint, url_prefix='/')
    app.register_blueprint(dataset_generation_blueprint)
    app.register_blueprint(training_blueprint)
    app.register_blueprint(combinatorics_method_blueprint)

    return app
