import os
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

class HemoglobinDataset(Dataset):
    def __init__(self, csv_file, image_dir):
        self.data = pd.read_csv(csv_file)

        self.image_dir = image_dir

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):

        patient_id = str(self.data.iloc[idx]["PATIENT_ID"])
        hb_level = float(self.data.iloc[idx]["HB_LEVEL_GperL"])

        image_path = os.path.join(
            self.image_dir,
            f"{patient_id}.jpg"
        )

        image = Image.open(image_path).convert("RGB")
        image = self.transform(image)

        return image, hb_level