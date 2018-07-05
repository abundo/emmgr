from flask import Flask
app = Flask(__name__, 
            template_folder = 'views',
        )

from emmgr.app.controller import api

from emmgr.app.controller import default
from emmgr.app.controller import elements
from emmgr.app.controller import tools
