import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import sys

# Load model
model = models.resnet18(weights=None)

num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 1)

model.load_state_dict(
    torch.load("../models/hb_predictor.pth")
)

model.eval()

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Load image
image_path = sys.argv[1]
image = Image.open(image_path)

# Transform image
image = transform(image).unsqueeze(0)

# Prediction
with torch.no_grad():

    hb_level = model(image)
predicted_hb=hb_level.item()/10
print(
    "Predicted Hemoglobin:",
    round(predicted_hb, 2),
    "g/dL"
)