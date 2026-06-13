import torch
import torch.nn as nn
import torch.optim as optim

from torchvision import models
from torch.utils.data import DataLoader

from hb_dataset import HemoglobinDataset

# Dataset
dataset = HemoglobinDataset(
    csv_file="../data/metadata.csv",
    image_dir="../data/images"
)

dataloader = DataLoader(
    dataset,
    batch_size=8,
    shuffle=True
)

# Model
model = models.resnet18(weights="DEFAULT")

num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 1)

# Loss + Optimizer
criterion = nn.MSELoss()
optimizer = optim.Adam(
    model.parameters(),
    lr=0.001
)

# Training
epochs = 20

for epoch in range(epochs):

    running_loss = 0.0

    for images, hb_values in dataloader:

        hb_values = hb_values.float().view(-1, 1)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, hb_values)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

    print(
        f"Epoch {epoch+1}/{epochs}, "
        f"Loss: {running_loss:.4f}"
    )

# Save Model
torch.save(
    model.state_dict(),
    "../models/hb_predictor.pth"
)

print("Hemoglobin Model Saved!")