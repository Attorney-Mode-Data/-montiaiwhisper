import os
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn.functional as F
from torch import Tensor
from torch.distributions import Categorical

from .audio import CHUNK_LENGTH
from .tokenizer import Tokenizer, get_tokenizer
from .utils import compression_ratio

if torch.cuda.is_available():
    _DEFAULT_DEVICE = "cuda"
elif torch.backends.mps.is_available():
    _DEFAULT_DEVICE = "mps"
else:
    _DEFAULT_DEVICE = "cpu"

# Allow override via environment variable
DEFAULT_DEVICE = os.environ.get("WHISPER_DEVICE", _DEFAULT_DEVICE)

@dataclass
class DecodingOptions:
    task: str = "transcribe"          # 'transcribe' or 'translate'
    language: Optional[str] = None    # language code, e.g. 'en'
    temperature: float = 0.0
    sample_len: Optional[int] = None  # maximum number of tokens to sample
    best_of: Optional[int] = None     # number of candidates when sampling with non-zero temperature
    beam_size: Optional[int] = 1      # beam size for beam search (1 = greedy)
    patience: Optional[float] = None  # patience for beam decay (used only if beam_size > 1)
    length_penalty: Optional[float] = None
    suppress_blank: bool = True
    suppress_tokens: Optional[List[int]] = None
    compression_ratio_threshold: Optional[float] = 2.4
    logprob_threshold: Optional[float] = -1.0
    no_speech_threshold: Optional[float] = 0.6
    condition_on_previous_text: bool = True
    initial_prompt: Optional[str] = None
    prefix: Optional[str] = None
    prompt_reset_on_temperature: Optional[float] = 0.5
    fp16: bool = True if DEFAULT_DEVICE in ("cuda", "mps") else False  # auto half-precision on GPU

@dataclass
class DecodingResult:
    text: str
    tokens: List[int]
    logprobs: Optional[List[float]] = None
    language: Optional[str] = None
    compression_ratio: Optional[float] = None
    avg_logprob: Optional[float] = None
    no_speech_prob: Optional[float] = None
    temperature: Optional[float] = None

class Decoding:
    def __init__(self, model, options: DecodingOptions):
        self.model = model
        self.options = options
        self.device = next(model.parameters()).device

    def detect_language(self, mel: Tensor, tokenizer: Tokenizer = None) -> Tuple[Tensor, List[dict]]:
        """
        Detect spoken language (cached version).
        Returns:
            language_tokens: ids of most probable language tokens
            language_probs: list of dicts with probabilities per language
        """
        if tokenizer is None:
            tokenizer = get_tokenizer(self.model.is_multilingual,
                                      num_languages=self.model.num_languages)

        # Use half precision if requested
        if self.options.fp16 and mel.dtype != torch.float16:
            mel = mel.half()
        elif not self.options.fp16 and mel.dtype != torch.float32:
            mel = mel.float()

        # Run encoder if not already done (simplified)
        # In original, encoder is called outside; here we ensure
        if not hasattr(self, "_encoder_output"):
            self._encoder_output = self.model.encoder(mel)
        encoder_output = self._encoder_output

        # Language detection logits from the model's decoder start token
        logits = self.model.logits(encoder_output, torch.tensor([[tokenizer.sot]]).to(self.device))
        lang_logits = logits[0, 0, tokenizer.sot_lang : tokenizer.sot_lang + self.model.num_languages]
        lang_probs = F.softmax(lang_logits.float(), dim=-1).cpu()
        top_lang_idx = lang_probs.argmax().item()
        lang_token = top_lang_idx + tokenizer.sot_lang

        language_probs = [
            {lang: p.item() for lang, p in zip(tokenizer.all_language_tokens, lang_probs)}
        ]
        return torch.tensor([lang_token]), language_probs

    # Simplified decode method (greedy/beam search). For full implementation,
    # refer to the original decoding.py. Here we show the core modification.
    def decode(self, mel: Tensor, **kwargs) -> DecodingResult:
        # Merge kwargs with self.options
        opts = self.options
        for k, v in kwargs.items():
            if hasattr(opts, k):
                setattr(opts, k, v)

        # Pre‑compute language if not given
        if opts.language is None and self.model.is_multilingual:
            lang_tokens, lang_probs = self.detect_language(mel)
            lang_token = lang_tokens[0].item()
            opts.language = self.model.tokenizer.decode([lang_token])
        else:
            lang_token = None

        # Greedy decoding (beam_size == 1)
        if opts.beam_size == 1:
            result = self._greedy_decode(mel, lang_token)
        else:
            result = self._beam_search_decode(mel, lang_token)  # not implemented here for brevity
        return result

    def _greedy_decode(self, mel: Tensor, lang_token: Optional[int]) -> DecodingResult:
        # Simplified greedy decode loop – real implementation would use kv-caching,
        # but for Android/Termux speed is less critical than memory.
        # This stub returns a dummy result; replace with actual logic from original.
        text = "MontiDroid decode (greedy)"
        tokens = [lang_token] if lang_token else []
        return DecodingResult(text=text, tokens=tokens)

@torch.no_grad()
def detect_language(
    model: "Whisper", mel: Tensor, tokenizer: Tokenizer = None
) -> Tuple[Tensor, List[dict]]:
    """
    Standalone language detection using the same logic as Decoding.detect_language.
    """
    decoder = Decoding(model, DecodingOptions())
    return decoder.detect_language(mel, tokenizer)
