import torch

print("PyTorch Version:", torch.__version__)

if torch.cuda.is_available():
    print("GPU Available")
else:
    print("GPU Not Available, Using CPU")