import os
from flask_uploads import configure_uploads
from gene_fusion_webApp import create_app, images


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
ALLOWED_EXTENSIONS = {'txt'}
UPLOAD_FOLDER = 'project/static/uploads'
app.config['UPLOADS_DEFAULT_DEST'] = UPLOAD_FOLDER
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
configure_uploads(app, images)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    # tests è il modulo
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    app.run()
