import sys
from argparse import Namespace

# Add the transformers directory to the Python path
sys.path.append('/home/u/transformers')

from transformers import pipeline
from custom_serving import ServeCommand

# Create a Namespace object with the required arguments
args = Namespace(
    host="localhost",
    port=8888,
    workers=1,
    task="translation"
)

# Initialize the pipeline
nlp = pipeline(
    task="translation",
    model="facebook/mbart-large-50-many-to-many-mmt",
    tokenizer="facebook/mbart-large-50-many-to-many-mmt",
)

# Create and run the custom server
server = ServeCommand(nlp, args.host, args.port, args.workers)
server.run()
