import os
import asyncio
import logging
from typing import Optional

from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

logger = logging.getLogger(__name__)

class ModelServer:
    def __init__(self, model_name: str = 'gpt2', device: str = 'cpu'):
        self.model_name = model_name
        self.device = device
        self._load_model()

    def _get_device_map(self):
        if self.device and 'cuda' in self.device.lower() and torch.cuda.is_available():
            return 0
        return -1

    def _load_model(self):
        logger.info('Loading model %s on device %s', self.model_name, self.device)
        # For small models: use pipeline for simplicity
        device = self._get_device_map()
        try:
            # Use AutoModel + tokenizer to have more control
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16 if device==0 and torch.cuda.is_available() else None)
            if device == 0 and torch.cuda.is_available():
                self.model.to('cuda')
            self.pipeline = pipeline('text-generation', model=self.model, tokenizer=self.tokenizer, device=device)
        except Exception as e:
            logger.exception('Failed loading model via from_pretrained, fallback to pipeline')
            self.pipeline = pipeline('text-generation', model=self.model_name, device=device)

    async def generate(self, prompt: str, max_new_tokens: int = 128, temperature: float = 0.7, top_p: float = 0.95, do_sample: bool = True) -> str:
        # Run generation in threadpool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_sync, prompt, max_new_tokens, temperature, top_p, do_sample)

    def _generate_sync(self, prompt, max_new_tokens, temperature, top_p, do_sample):
        params = dict(max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p, do_sample=do_sample)
        logger.debug('Generating with params: %s', params)
        out = self.pipeline(prompt, **params)
        # pipeline returns list of dicts
        text = out[0]['generated_text'] if isinstance(out, list) else str(out)
        # If the pipeline prepends the prompt, return only the continuation? We'll return full generated_text for transparency.
        return text
