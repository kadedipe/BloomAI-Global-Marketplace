import argparse

def get_train_args():
    parser = argparse.ArgumentParser(description='Train a neural network on a dataset')
    parser.add_argument('data_dir', type=str, help='Path to the dataset directory')
    parser.add_argument('--save_dir', type=str, default='checkpoint.pth', help='Directory to save the checkpoint')
    parser.add_argument('--arch', type=str, default='vgg16', choices=['vgg16', 'resnet18', 'densenet121'], help='Architecture (vgg16, resnet18, densenet121)')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--hidden_units', type=int, default=512, help='Number of hidden units in the classifier')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--gpu', action='store_true', help='Use GPU for training')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = get_train_args()
    print(args)