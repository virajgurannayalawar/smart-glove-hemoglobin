import torch
import torch.nn as nn
import torch.optim as optim

from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader

# Image Transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Load Dataset
dataset = datasets.ImageFolder(
    root="../data",
    transform=transform
)

dataloader = DataLoader(
    dataset,
    batch_size=2,
    shuffle=True
)

# Load Pretrained Model
model = models.resnet18(pretrained=True)

# Change final layer
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 2)

# Loss and Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training
epochs = 3

for epoch in range(epochs):

    running_loss = 0.0

    for images, labels in dataloader:

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss}")

# Save model
torch.save(model.state_dict(), "../models/anemia_detector.pth")

print("Model Saved Successfully!")