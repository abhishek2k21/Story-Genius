import torch
import sys

def check_gpu():
    print(f"Python: {sys.version}")
    try:
        is_available = torch.cuda.is_available()
        print(f"CUDA Available: {is_available}")
        if is_available:
            print(f"Device Name: {torch.cuda.get_device_name(0)}")
            print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        else:
            print("No NVIDIA GPU detected compatible with PyTorch.")
    except ImportError:
        print("Torch not installed.")

if __name__ == "__main__":
    check_gpu()
