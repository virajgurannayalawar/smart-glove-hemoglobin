import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

# Load model
model = models.resnet18(pretrained=False)

num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 2)

model.load_state_dict(
    torch.load("../models/anemia_detector.pth")
)

model.eval()

# Classes
classes = ['anemia', 'normal']

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Load image
image = Image.open("../data/test/test1.jpg")

# Transform image
image = transform(image).unsqueeze(0)

# Prediction
with torch.no_grad():

    outputs = model(image)

    _, predicted = torch.max(outputs, 1)

    prediction = classes[predicted.item()]

print("Prediction:", prediction)