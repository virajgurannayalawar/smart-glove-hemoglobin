from dataclasses import dataclass
from typing import Optional

from app.core.config import settings


class ModelPredictionError(RuntimeError):
    pass


@dataclass(frozen=True)
class HemoglobinPrediction:
    hemoglobin_level: float
    provider: str
    notes: Optional[str] = None


async def predict_hemoglobin_from_image(image_bytes: bytes) -> HemoglobinPrediction:
    """
    Backend-side prediction hook.

    Chunk 4: we provide a stable interface and a safe 'mock' provider.
    Next chunks can add a real provider (ONNX/Torch/etc.) without changing routes.
    """
    if not image_bytes:
        raise ModelPredictionError("Empty image payload")

    if settings.MODEL_PROVIDER == "mock":
        return HemoglobinPrediction(
            hemoglobin_level=float(settings.MOCK_HEMOGLOBIN_VALUE),
            provider="mock",
            notes="Mock predictor (replace with real model provider)",
        )

    raise ModelPredictionError(f"Unsupported MODEL_PROVIDER: {settings.MODEL_PROVIDER}")

