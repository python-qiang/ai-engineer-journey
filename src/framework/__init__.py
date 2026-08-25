# TODO: Remove this once we have a unified entry point (e.g. FastAPI main.py in Week 17)
# that explicitly calls logging setup. For now, this ensures logger auto-setup triggers
# whenever any module imports from the framework package.
import framework.logger  # noqa: F401
