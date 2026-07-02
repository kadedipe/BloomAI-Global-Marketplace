#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# */UDACITY/finalpyproject-load-preprocess-images/load_and_preprocessing_the_image_dataset.py
#                                                                             
# PROGRAMMER: Kolapo Adedipe
# DATE CREATED: July 27, 2023                    
# REVISED DATE: 
# PURPOSE: Create a function load_and_preprocessing_the_image_dataset that process the images 
#          of dataset indicate whether it is a flower. 
#
# Define the data directories
data_dir = 'flowers'
train_dir = data_dir + '/train'
valid_dir = data_dir + '/valid'
test_dir = data_dir + '/test'

# Define transforms for the training, validation, and testing sets
# We will apply random scaling, cropping, and flipping for training data,
# and only resizing and center cropping for validation and testing data.
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
    ]),
    'test': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
}

# Load the datasets with ImageFolder
image_datasets = {
    'train': datasets.ImageFolder(train_dir, transform=data_transforms['train']),
    'valid': datasets.ImageFolder(valid_dir, transform=data_transforms['valid']),
    'test': datasets.ImageFolder(test_dir, transform=data_transforms['test'])
}

# Using the image datasets and the transforms, define the dataloaders
dataloaders = {
    'train': torch.utils.data.DataLoader(image_datasets['train'], batch_size=64, shuffle=True),
    'valid': torch.utils.data.DataLoader(image_datasets['valid'], batch_size=32),
    'test': torch.utils.data.DataLoader(image_datasets['test'], batch_size=32)
}

# Load category label to category name mapping from 'cat_to_name.json'
with open('cat_to_name.json', 'r') as f:
    cat_to_name = json.load(f)

