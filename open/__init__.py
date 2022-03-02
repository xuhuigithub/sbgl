from flask import Blueprint

open = Blueprint("open", __name__)

from . import profile
from . import data