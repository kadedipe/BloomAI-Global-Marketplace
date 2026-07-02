"""
Author: Kolapo Adedipe
Date: October 03, 2023
Description: A script for training a neural network on a dataset and saving the model as a checkpoint.
"""

import argparse
import torch
from torch import nn, optim
from torchvision import datasets, transforms, models
from collections import OrderedDict
import os
import datetime  # Import datetime to include the date
from download_models import download_all, extract_dataset
from config import DATASET_DIR

download_all()
extract_dataset()

data_dir = str(DATASET_DIR)

def load_data(data_dir):
    # Define data transforms
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'valid': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    }

    # Load datasets
    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x])
                      for x in ['train', 'valid']}
    
    # Create dataloaders
    dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=32, shuffle=True)
                   for x in ['train', 'valid']}
    
    return dataloaders

def build_model(arch, hidden_units):
    # Load pre-trained model
    model = getattr(models, arch)(pretrained=True)

    # Freeze pre-trained model parameters
    for param in model.parameters():
        param.requires_grad = False

    # Build a custom classifier
    classifier = nn.Sequential(OrderedDict([
        ('fc1', nn.Linear(25088, hidden_units)),
        ('relu', nn.ReLU()),
        ('fc2', nn.Linear(hidden_units, 102)),
        ('output', nn.LogSoftmax(dim=1))
    ]))

    # Replace the pre-trained classifier with the custom one
    model.classifier = classifier

    return model

def train_model(model, dataloaders, criterion, optimizer, device, epochs=10):
    model.to(device)
    for epoch in range(epochs):
        # Training phase
        model.train()
        running_loss = 0.0
        for inputs, labels in dataloaders['train']:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        
        train_loss = running_loss / len(dataloaders['train'])

        # Validation phase
        model.eval()
        validation_loss = 0.0
        accuracy = 0
        with torch.no_grad():
            for inputs, labels in dataloaders['valid']:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                validation_loss += loss.item()
                ps = torch.exp(outputs)
                top_p, top_class = ps.topk(1, dim=1)
                equals = top_class == labels.view(*top_class.shape)
                accuracy += torch.mean(equals.type(torch.FloatTensor))
        
        validation_loss = validation_loss / len(dataloaders['valid'])
        accuracy = accuracy / len(dataloaders['valid'])
        
        print(f"Epoch {epoch + 1}/{epochs}, "
              f"Train Loss: {train_loss:.4f}, "
              f"Validation Loss: {validation_loss:.4f}, "
              f"Validation Accuracy: {accuracy*100:.2f}%")

def save_checkpoint(model, arch, hidden_units, save_dir):
    checkpoint = {
        'arch': arch,
        'hidden_units': hidden_units,
        'state_dict': model.state_dict(),
        'class_to_idx': model.class_to_idx,
        'epochs': epochs,
        'optimizer_state_dict': optimizer.state_dict(),
        'date_created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    torch.save(checkpoint, save_dir)

def main():
    parser = argparse.ArgumentParser(description='Train a neural network on a dataset')

    parser.add_argument('data_dir', type=str, help='Path to the dataset directory')

    parser.add_argument('--save_dir', type=str, default='checkpoint.pth')

    parser.add_argument('--arch', type=str, default='vgg16')

    parser.add_argument('--learning_rate', type=float, default=0.001)

    parser.add_argument('--hidden_units', type=int, default=512)

    parser.add_argument('--epochs', type=int, default=10)

    parser.add_argument('--gpu', action='store_true')

    args = parser.parse_args()

    # Download models and dataset if they are missing
    download_all()
    extract_dataset()

    data_dir = args.data_dir
    save_dir = args.save_dir
    arch = args.arch
    learning_rate = args.learning_rate
    hidden_units = args.hidden_units
    epochs = args.epochs
    use_gpu = args.gpu

    device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")

    dataloaders = load_data(data_dir)
    model = build_model(arch, hidden_units)
    criterion = nn.NLLLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=learning_rate)
    
    train_model(model, dataloaders, criterion, optimizer, device, epochs)
    save_checkpoint(model, arch, hidden_units, save_dir)

if __name__ == '__main__':
    main()