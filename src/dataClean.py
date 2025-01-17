#### CLEANS THE MERGED DATASET
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MultiLabelBinarizer
from src import config
import logging.config
import logging

logging.config.fileConfig(config.LOGGING_CONFIG, disable_existing_loggers=False)
logger = logging.getLogger('dataClean')

def preliminaryClean(merged, selectedColumns):
    """ Performs a preliminary cleaning of the merged dataset.
        Selects the columns we need for the model and drops NA rows
    Args:
        merged (pandas dataframe): the merged dataset combining Desserts Dataset and Epicurious Recipes Dataset
        selectedColumns (list): the columns that should be included after this point
                                columns that are needed for the prediction or recommendation system
    Returns:
        data (pandas dataframe): a verson of the merged dataset that has undergone preliminary cleaning
    """
    # Select only the columns we are interested in to make processing faster
    try:
        data = merged[selectedColumns]
    except Exception:
        logger.error("Expected column names not in the merged dataset. Please check that these columns exist in the raw "
                     "data: {}.".format(config.selectedColumns))
        raise
    # Drop all NAs (recipe_name and aggregateRating should NOT be missing, but flavors has around 100 Na values)
    data = data.dropna()
    data = data.reset_index(drop=True)
    return data

def fixFlavors(data):
    """ Uses regex to fix misspellings in flavors and clarify ambiguous flavors.
        Cleans the flavors column and turns it into a list of flavors
    Args:
        data (pandas dataframe): a verson of the merged dataset that has undergone preliminary cleaning
    Returns:
        data (pandas dataframe): a version of the input dataframe with fixed flavors
    """
    ## Fix misspellings
    # Change occurrences of "tomatoe" to "tomato
    data['flavors'] = data['flavors'].replace('tomatoe', 'tomato', regex=True)
    # Change occurrences of "whisky" to "whiskey"
    data['flavors'] = data['flavors'].replace('whisky', 'whiskey', regex=True)
    ## Clarify ambiguous flavors (use an underscore so we can later separate it with a space using regex)
    # Change occurrences of "bay" to "bay_leaf"
    data['flavors'] = data['flavors'].replace('bay', 'bay_leaf', regex=True)
    # Change occurrences of "earl" to "earl_grey"
    data['flavors'] = data['flavors'].replace('earl', 'earl_grey', regex=True)
    # Change occurrences of "graham" to "graham_cracker"
    data['flavors'] = data['flavors'].replace('graham', 'graham_cracker', regex=True)
    ## Clean the flavors column
    # Flavors is a string, but we want it to be a list. Split it by spaces and make it into a list.
    data["flavors"] = data.apply(lambda flavorString: flavorString["flavors"].split(" "), axis=1)
    # Get rid of repeated flavors for each recipe
    data["flavors"] = data["flavors"].apply(np.unique)
    return data

def oneHotEncode(data):
    """ One hot encodes all of the flavors in the data using the MultiLabelBinarizer from sklearn.preprocessing """
    mlb = MultiLabelBinarizer()
    data = data.join(pd.DataFrame(mlb.fit_transform(data.pop('flavors')),
                                  columns=mlb.classes_,
                                  index=data.index))
    return data

def getUniqueFlavors(data):
    """ Gets a list of all the unique flavors in the dataset (equivalent to the list of one-hot-encoded flavor columns)
        Saves the unique flavors as a list in json format to the data/model directory (for use in the prediction process)
    Args:
        data (pandas dataframe): a version of the cleaned data with fixed flavors
        flavorPath (str): location where the list of unique flavors should be stored
    Returns:
        none
    """
    uniqueFlavors = set()
    for flavorList in data['flavors']:
        # Use update to unclude only the unique values in the set
        uniqueFlavors.update(flavorList)
    uniqueFlavors = sorted(uniqueFlavors)
    return uniqueFlavors

def run():
    """ Runs all the functions to clean the merged dataset
        Performs a preliminary clean, cleans the flavors column, and one-hot encodes the flavors
    """
    logger.info("Beginning to clean the merged dataset...")
    # Load the merged data and perform a preliminary clean
    merged = pd.read_csv(config.MERGED_PATH)
    data= preliminaryClean(merged, config.SELECTED_COLUMNS)
    # Clean the dataset by fixing the flavors.
    clean = fixFlavors(data)
    # Save the dataset at this stage for recommendations
    clean.to_csv(config.CLEAN_PATH, index = False)
    # Get the unique list of flavors and save them to the model directory
    uniqueFlavors = getUniqueFlavors(clean)
    with open(config.FLAVOR_PATH, 'w') as filehandle:
        json.dump(uniqueFlavors, filehandle)
    # One hot encode the cleaned data
    final = oneHotEncode(clean)
    logger.debug("The cleaned dataframe has the following columns: {}".format(final.columns))
    # Save the one hot encoded data for model fitting and predictions
    final.to_csv(config.FINAL_PATH, index = False)
    logger.info("Successfully cleaned the merged dataset. The data can now be fit to a model.")
