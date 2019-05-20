import logging

#Logging utility to print to terminal for debugging

global logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)