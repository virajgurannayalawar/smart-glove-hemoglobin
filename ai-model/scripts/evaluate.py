import torch
import pandas as pd
from PIL import Image
from torchvision import transforms, models
import torch.nn as nn

# Load metadata
df = pd.read_csv("../data/metadata.csv")

# Load model
model = models.resnet18(pretrained=False)

num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 1)

model.load_state_dict(
    torch.load("../models/hb_predictor.pth")
)

model.eval()

# Transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

total_error = 0
count = 0

for _, row in df.iterrows():

    image_id = row["PATIENT_ID"]
    actual_hb = row["HB_LEVEL_GperL"] / 10

    image_path = f"../data/images/{image_id}.jpg"

    try:
        image = Image.open(image_path)

        image = transform(image).unsqueeze(0)

        with torch.no_grad():
            predicted_hb = model(image).item() / 10

        error = abs(predicted_hb - actual_hb)

        total_error += error
        count += 1

    except:
        pass

print("Images Tested:", count)
print("Average Error:", round(total_error / count, 2), "g/dL")