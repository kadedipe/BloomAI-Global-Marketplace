import torch
from torch import nn
from torchvision import models

def load_checkpoint(filepath, input_features):
    """
    Load a trained model checkpoint from a file.

    Args:
        filepath (str): Path to the checkpoint file.
        input_features (int): Number of input features for the model.

    Returns:
        torch.nn.Module: Loaded model.
    """
    checkpoint = torch.load(filepath)
    arch = checkpoint['arch']
    hidden_units = checkpoint['hidden_units']
    
    # Dynamically select the model architecture based on user input
    if arch == 'vgg16':
        model = models.vgg16(pretrained=True)
        input_size = 25088  # VGG16 has 25088 input features
    elif arch == 'resnet18':
        model = models.resnet18(pretrained=True)
        input_size = 512  # ResNet18 has 512 input features
    elif arch == 'densenet121':
        model = models.densenet121(pretrained=True)
        input_size = 1024  # DenseNet121 has 1024 input features
    else:
        raise ValueError("Unsupported architecture: " + arch)
    
    # Modify the classifier to match the expected input features
    classifier = nn.Sequential(
        nn.Linear(input_size, hidden_units),
        nn.ReLU(),
        nn.Linear(hidden_units, 102),
        nn.LogSoftmax(dim=1)
    )
    
    model.classifier = classifier
    model.load_state_dict(checkpoint['state_dict'])
    
    return model