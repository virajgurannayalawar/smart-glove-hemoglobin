import os
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# Image transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Load dataset
dataset = datasets.ImageFolder(
    root="../data",
    transform=transform
)

# Create dataloader
dataloader = DataLoader(
    dataset,
    batch_size=2,
    shuffle=True
)

# Print dataset info
print("Classes:", dataset.classes)
print("Total Images:", len(dataset))

# Test loading
for images, labels in dataloader:
    print("Image batch shape:", images.shape)
    print("Labels:", labels)
    break