# Implementation Review and Plan

## What has been implemented so far

1. `ai-model/scripts/train.py`
   - A training script was created.
   - It loads images from `../data` using `torchvision.datasets.ImageFolder`.
   - It uses a pretrained `ResNet18` model.
   - The final layer is changed to output 2 values.
   - It trains for 3 epochs with `CrossEntropyLoss`.
   - The model is saved to `ai-model/models/anemia_detector.pth`.

2. `ai-model/scripts/predict.py`
   - A prediction script loads `anemia_detector.pth`.
   - It preprocesses one input image.
   - It predicts one of two classes: `anemia` or `normal`.


---

## Why this is not complete

- The requirement is to predict a numeric hemoglobin value, such as `12.5 g/dL`.
- The current model is a binary classifier, not a regression model.
- The current code only returns `anemia` vs `normal`, not a numeric hemoglobin level.
- There is no evidence that a Kaggle dataset with hemoglobin labels was used.


---

## What needs to be implemented next

### 1. Correct prediction target
- Change the model from classification to regression.
- The model output should be a single number representing hemoglobin level.
- Example: use `nn.Linear(num_features, 1)` and `nn.MSELoss()` or `nn.L1Loss()`.

### 2. Proper dataset usage
- Use a real dataset that contains images plus numeric hemoglobin labels.
- Prefer open-source data from Kaggle or another trusted source.
- Add dataset parsing that reads labels from metadata or a CSV file.

### 3. Training pipeline improvements
- Add train/validation/test split.
- Add image preprocessing and augmentation for finger images.
- Track metrics such as MAE, RMSE, and R².
- Save the best model based on validation performance.

### 4. Production readiness
- Add reproducibility with fixed random seeds and model versioning.
- Add evaluation logging and a performance summary.
- Add input validation and error handling in prediction code.



### 6. Testing
- Validate model performance on a held-out test set.
- Confirm the backend returns a numeric hemoglobin result.
- Add or update backend tests to cover real inference behavior.

---

## Instructions for the ai engineer

1. Pull the latest backend code before starting work:
   - `git pull origin main`
2. Use a real open-source dataset from Kaggle or another trusted source.
3. Change the model from classification to regression.
4. Add a proper train/validation/test split and regression metrics.


---

## Summary

- ✅ A prototype exists and a model file was saved.
- ❌ It is not the correct hemoglobin-value prediction model.
- ✅ The next goal is a real regression model, correct dataset usage, and backend integration.
