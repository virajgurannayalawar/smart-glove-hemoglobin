from dataclasses import dataclass
from typing import Optional
from io import BytesIO
import logging
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelPredictionError(RuntimeError):
    pass


@dataclass(frozen=True)
class HemoglobinPrediction:
    HemoglobinLevel: float
    Provider: str
    Notes: Optional[str] = None


# Global variable to cache loaded PyTorch model
_model = None


def get_pytorch_model() -> nn.Module:
    """
    Load ResNet18 model structure and weights from the pth file.
    Caches the loaded model in memory to avoid reloading on every request.
    """
    global _model
    if _model is not None:
        return _model

    try:
        # Define model architecture matching training script: ResNet18
        model = models.resnet18(weights=None)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, 1)

        # Load weights on CPU (safe for all servers/environments)
        model.load_state_dict(
            torch.load(settings.MODEL_PATH, map_location=torch.device("cpu"))
        )
        model.eval()
        _model = model
        logger.info(f"Successfully loaded PyTorch model from {settings.MODEL_PATH}")
        return _model
    except Exception as e:
        logger.exception("Failed to load PyTorch model weights")
        raise ModelPredictionError(f"Failed to load model weights: {e}")


async def predict_hemoglobin_from_image(image_bytes: bytes) -> HemoglobinPrediction:
    """
    Predicts hemoglobin level from preprocessed image bytes using the configured provider.
    """
    if not image_bytes:
        raise ModelPredictionError("Empty image payload")

    if settings.MODEL_PROVIDER == "mock":
        return HemoglobinPrediction(
            HemoglobinLevel=float(settings.MOCK_HEMOGLOBIN_VALUE),
            Provider="mock",
            Notes="Mock predictor (replace with real model provider)",
        )

    elif settings.MODEL_PROVIDER == "pytorch":
        try:
            # 1. Open preprocessed image using PIL
            img = Image.open(BytesIO(image_bytes)).convert("RGB")

            # 2. Define transforms (matching predict.py / train.py)
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor()
            ])

            # 3. Apply transformations and add batch dimension (B, C, H, W)
            tensor = transform(img).unsqueeze(0)

            # 4. Get the loaded model
            model = get_pytorch_model()

            # 5. Run inference
            with torch.no_grad():
                output = model(tensor)

            # 6. Extract raw model output (which represents HB_LEVEL_GperL)
            # Convert to g/dL by dividing by 10 (as in predict.py)
            predicted_hb_g_dl = output.item() / 10.0

            return HemoglobinPrediction(
                HemoglobinLevel=round(predicted_hb_g_dl, 2),
                Provider="pytorch",
                Notes="PyTorch ResNet18 predictor",
            )
        except Exception as e:
            logger.exception("Inference failed")
            raise ModelPredictionError(f"Inference failed: {e}")

    raise ModelPredictionError(f"Unsupported MODEL_PROVIDER: {settings.MODEL_PROVIDER}")
