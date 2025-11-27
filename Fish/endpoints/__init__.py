from .routes import bp_ui
from .auth import bp_auth
from .upload import bp_upload
from .api_llm import bp_llm
from .api_security import bp_security
from .analysis import bp_analysis

def register_blueprints(app):
    """
    Register all endpoint blueprints on the provided Flask app.
    """
    app.register_blueprint(bp_ui)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_upload)
    app.register_blueprint(bp_llm)
    app.register_blueprint(bp_security)
    app.register_blueprint(bp_analysis)
