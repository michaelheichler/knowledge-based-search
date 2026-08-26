import mlx.core as mx
from mlx import nn
from mlx_embeddings.models.lfm2 import Lfm2Model
from mlx_lm.models.cache import ArraysCache, KVCache
from mlx_lm.models.lfm2 import ModelArgs


class Lfm2EmbeddingModel(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.model = Lfm2Model(ModelArgs.from_dict(config))

    def __call__(self, input_ids: mx.array) -> mx.array:
        return self.model(input_ids, cache=self.make_cache)

    def sanitize(self, weights: dict) -> dict:
        sanitized = {}
        for key, value in weights.items():
            new_key = key if key.startswith("model.") else f"model.{key}"
            if "conv.conv.weight" in new_key and value.shape[-1] > value.shape[1]:
                value = value.transpose(0, 2, 1)
            sanitized[new_key] = value
        return sanitized

    @property
    def make_cache(self) -> list:
        return [
            KVCache() if layer.is_attention_layer else ArraysCache(size=1)
            for layer in self.model.layers
        ]


def build_model(config: dict) -> Lfm2EmbeddingModel:
    return Lfm2EmbeddingModel(config)


def mean_pool(hidden_states: mx.array, attention_mask: mx.array) -> mx.array:
    mask = attention_mask[:, :, None]
    summed = mx.sum(hidden_states * mask, axis=1)
    counts = mx.maximum(mx.sum(mask, axis=1), 1e-9)
    return summed / counts
