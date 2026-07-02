import argparse

def get_predict_args():
    parser = argparse.ArgumentParser(description='Predict flower name from an image')
    parser.add_argument('image_path', type=str, help='Path to the input image')
    parser.add_argument('checkpoint', type=str, help='Path to the checkpoint file')
    parser.add_argument('--top_k', type=int, default=1, help='Return top K most likely classes')
    parser.add_argument('--category_names', type=str, help='Path to category names mapping JSON file')
    parser.add_argument('--gpu', action='store_true', help='Use GPU for inference')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = get_predict_args()
    print(args)