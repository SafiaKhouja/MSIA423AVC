import traceback
import numpy as np
from flask import render_template, request, redirect, url_for
import logging.config
from flask import Flask
from src.buildInputDB import input
from flask_sqlalchemy import SQLAlchemy
from src import predict



# Initialize the Flask application
app = Flask(__name__, template_folder="app/templates")

# Configure flask app from flask_config.py
app.config.from_pyfile('config/flaskconfig.py')

# Define LOGGING_CONFIG in flask_config.py - path to config file for setting
# up the logger (e.g. config/logging/local.conf)
logging.config.fileConfig(app.config["LOGGING_CONFIG"])
logger = logging.getLogger(app.config["APP_NAME"])
logger.debug('Test log')

# Initialize the database
db = SQLAlchemy(app)



@app.route('/')
def index():
    """Main view that lists songs in the database.

    Create view into index page that uses data queried from Track database and
    inserts it into the msiapp/templates/index.html template.

    Returns: rendered html template

    """
    return render_template('index.html')

@app.route('/prediction', methods=['POST'])
def add_entry():
    """View that process a POST with new song input

    :return: redirect to index page
    """
    #try:
    userInput = input(flavor1=request.form['flavor1'], flavor2=request.form['flavor2'], flavor3=request.form['flavor3'])
    db.session.add(userInput)
    db.session.commit()
    entry = db.session.query(input).order_by(input.id.desc()).first()
    prediction, flavorCombo, topRec, secondTopRec = predict.make_prediction(entry)
    #logger.info("New song added: %s by %s", request.form['Flavor 1'], request.form['Flavor 1'])
    return render_template("prediction.html", prediction = prediction, flavorCombo = flavorCombo,
                           noRecommendation = topRec[5],
                           topRecDessert = topRec[0], topRecURL = topRec[1], topRecRating= topRec[2], topRecReviewsCount= topRec[3],
                           secondTopRecDessert = secondTopRec[0], secondTopRecURL = secondTopRec[1],
                                secondTopRecRating=secondTopRec[2], secondTopRecReviewsCount = secondTopRec[3])



if __name__ == '__main__':
    print(db)
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"], host=app.config["HOST"])
