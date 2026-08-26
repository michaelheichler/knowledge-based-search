import os
import platform
import sys

MLX_MODEL_ID = "LiquidAI/LFM2.5-Embedding-350M"
GGUF_REPO_ID = "LiquidAI/LFM2.5-Embedding-350M-GGUF"
GGUF_FILENAME = "LFM2.5-Embedding-350M-Q4_K_M.gguf"


def is_apple_silicon() -> bool:
    return sys.platform == "darwin" and platform.machine() == "arm64"


def load_encoder():
    if is_apple_silicon():
        return _load_mlx_encoder()
    return _load_gguf_encoder()


def _download_mlx_files(repo_id):
    from huggingface_hub import hf_hub_download

    return {
        name: hf_hub_download(repo_id, name)
        for name in ("config.json", "tokenizer.json", "model.safetensors")
    }


def _build_mlx_model(files):
    import json

    import lfm2_embed
    import mlx.core as mx

    with open(files["config.json"], encoding="utf-8") as handle:
        config = json.load(handle)
    model = lfm2_embed.build_model(config)
    weights = mx.load(files["model.safetensors"])
    model.load_weights(list(model.sanitize(weights).items()))
    mx.eval(model.parameters())
    return model


def _load_mlx_encoder():
    import lfm2_embed
    import mlx.core as mx
    from tokenizers import Tokenizer

    repo_id = os.environ.get("KBS_EMBED_MODEL_ID", MLX_MODEL_ID)
    files = _download_mlx_files(repo_id)
    model = _build_mlx_model(files)
    tokenizer = Tokenizer.from_file(files["tokenizer.json"])

    def encode(texts):
        encodings = tokenizer.encode_batch(list(texts))
        input_ids = mx.array([item.ids for item in encodings])
        attention_mask = mx.array(
            [item.attention_mask for item in encodings], dtype=mx.float32
        )
        hidden_states = model(input_ids)
        pooled = lfm2_embed.mean_pool(hidden_states, attention_mask)
        mx.eval(pooled)
        return pooled.tolist()

    return encode


def _load_gguf_encoder():
    from llama_cpp import Llama

    repo_id = os.environ.get("KBS_EMBED_GGUF_REPO", GGUF_REPO_ID)
    filename = os.environ.get("KBS_EMBED_GGUF_FILE", GGUF_FILENAME)
    llama = Llama.from_pretrained(
        repo_id=repo_id, filename=filename, embedding=True, verbose=False
    )

    def encode(texts):
        response = llama.create_embedding(list(texts))
        return [row["embedding"] for row in response["data"]]

    return encode
