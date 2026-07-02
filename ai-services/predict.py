import argparse
import torch
from torch import nn
from torchvision import models, transforms
import json
from PIL import Image
import os
import datetime  # Import datetime to include the date
from download_models import download_all

download_all()

# Author: Kolapo Adedipe
# Date Created: 2023-10-03  (Replace with the actual date)
# Description: This script predicts the flower name from an input image using a trained neural network.

def load_checkpoint(filepath):
    """
    Load a trained model checkpoint from a file.

    Args:
        filepath (str): Path to the checkpoint file.

    Returns:
        torch.nn.Module: Loaded model.
    """
    checkpoint = torch.load(filepath)
    arch = checkpoint['arch']
    hidden_units = checkpoint['hidden_units']
    model = getattr(models, arch)(pretrained=True)
    model.classifier = nn.Sequential(
        nn.Linear(25088, hidden_units),
        nn.ReLU(),
        nn.Linear(hidden_units, 102),
        nn.LogSoftmax(dim=1)
    )
    model.load_state_dict(checkpoint['state_dict'])
    return model

def process_image(image_path):
    """
    Process an input image.

    Args:
        image_path (str): Path to the input image.

    Returns:
        torch.Tensor: Processed image as a PyTorch tensor.
    """
    image = Image.open(image_path)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    image = preprocess(image)
    return image

def predict(image_path, model, topk=5, category_names=None, device='cuda'):
    """
    Predict the class of an input image.

    Args:
        image_path (str): Path to the input image.
        model (torch.nn.Module): Trained model for prediction.
        topk (int): Return top K most likely classes.
        category_names (str): Path to category names mapping JSON file.
        device (str): Device for inference ('cuda' or 'cpu').

    Returns:
        tuple: Tuple containing probabilities and labels.
    """
    model.to(device)
    model.eval()
    
    image = process_image(image_path)
    image = image.unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(image)
        ps = torch.exp(output)
        top_p, top_class = ps.topk(topk, dim=1)
    
    if category_names:
        with open(category_names, 'r') as f:
            cat_to_name = json.load(f)
        labels = [cat_to_name[str(cls)] for cls in top_class[0].cpu().numpy()]
    else:
        labels = top_class[0].cpu().numpy()
    
    probabilities = top_p[0].cpu().numpy()
    
    return probabilities, labels

def main():
    parser = argparse.ArgumentParser(description='Predict flower name from an image')
    parser.add_argument('image_path', type=str, help='Path to the input image')
    parser.add_argument('checkpoint', type=str, help='Path to the checkpoint file')
    parser.add_argument('--top_k', type=int, default=1, help='Return top K most likely classes')
    parser.add_argument('--category_names', type=str, help='Path to category names mapping JSON file')
    parser.add_argument('--gpu', action='store_true', help='Use GPU for inference')
    
    args = parser.parse_args()
    
    image_path = args.image_path
    checkpoint = args.checkpoint
    top_k = args.top_k
    category_names = args.category_names
    use_gpu = args.gpu
    
    device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
    
    model = load_checkpoint(checkpoint)
    probabilities, labels = predict(image_path, model, top_k, category_names, device)
    
    for i in range(len(labels)):
        print(f"Class: {labels[i]}, Probability: {probabilities[i]*100:.2f}%")

if __name__ == '__main__':
    main()