from flask import Flask
app = Flask(__name__, 
            template_folder = 'views',
        )

from app.controller import api

from app.controller import default
from app.controller import elements
from app.controller import tools
