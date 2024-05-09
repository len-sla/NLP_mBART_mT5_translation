import os
import sys

# Add the transformers directory to the Python path
sys.path.append('/home/u/transformers')

from argparse import ArgumentParser, Namespace
from typing import Any, List, Optional

from transformers.pipelines import Pipeline, get_supported_tasks, pipeline
from transformers.utils import logging
from transformers.commands import BaseTransformersCLICommand

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.routing import APIRoute
    from pydantic import BaseModel
    from starlette.responses import JSONResponse
    from uvicorn import run

    _serve_dependencies_installed = True
except (ImportError, AttributeError):
    BaseModel = object

    def Body(*x, **y):
        pass

    _serve_dependencies_installed = False

logger = logging.get_logger("transformers-cli/serving")

def serve_command_factory(args: Namespace):
    """
    Factory function used to instantiate serving server from provided command line arguments.

    Returns: ServeCommand
    """
    nlp = pipeline(
        task="translation",
        model="facebook/mbart-large-50-many-to-many-mmt",
        tokenizer="facebook/mbart-large-50-many-to-many-mmt",
        src_lang="en",  # Set the default source language
        tgt_lang="de"  # Set the default target language
    )
    return ServeCommand(nlp, args.host, args.port, args.workers)

class ServeCommand(BaseTransformersCLICommand):
    @staticmethod
    def register_subcommand(parser: ArgumentParser):
        """
        Register this command to argparse so it's available for the transformer-cli

        Args:
            parser: Root parser to register command-specific arguments
        """
        serve_parser = parser.add_parser(
            "serve", help="CLI tool to run inference requests through REST and GraphQL endpoints."
        )
        serve_parser.add_argument("--host", type=str, default="localhost", help="Interface the server will listen on.")
        serve_parser.add_argument("--port", type=int, default=8888, help="Port the serving will listen to.")
        serve_parser.add_argument("--workers", type=int, default=1, help="Number of http workers")
        serve_parser.set_defaults(func=serve_command_factory)

    def __init__(self, pipeline: Pipeline, host: str, port: int, workers: int):
        self._pipeline = pipeline

        self.host = host
        self.port = port
        self.workers = workers

        if not _serve_dependencies_installed:
            raise RuntimeError(
                "Using serve command requires FastAPI and uvicorn. "
                'Please install transformers with [serving]: pip install "transformers[serving]". '
                "Or install FastAPI and uvicorn separately."
            )
        else:
            logger.info(f"Serving model over {host}:{port}")
            self._app = FastAPI()
            self._app.add_api_route("/translate", self.translate, methods=["POST"])

    def run(self):
        run(self._app, host=self.host, port=self.port, workers=self.workers)

    async def translate(self, inputs: str = Query(...), src_lang: Optional[str] = None, tgt_lang: Optional[str] = None):
        try:
            # Split the input into source text
            source_text = inputs

            # Use default values if src_lang and tgt_lang are not provided
            if src_lang is None:
                src_lang = "en"
            if tgt_lang is None:
                tgt_lang = "de"

            # Perform translation using the mBART model
            translation = self._pipeline(source_text, src_lang=src_lang, tgt_lang=tgt_lang)
            return {"translation": translation}
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e)})
