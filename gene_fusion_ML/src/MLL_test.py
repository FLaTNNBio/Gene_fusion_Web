import torch
from torch_geometric.loader import DataLoader
from torch_geometric.nn import HypergraphConv, global_mean_pool
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, confusion_matrix
import json

# Define the HGCN model structure
class HGCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(HGCN, self).__init__()
        self.conv1 = HypergraphConv(in_channels, hidden_channels)
        self.conv2 = HypergraphConv(hidden_channels, hidden_channels)
        self.fc = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        x = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = global_mean_pool(x, batch)  # Pool the node embeddings to obtain graph embeddings
        x = self.fc(x)
        return F.log_softmax(x, dim=1)

# Function to evaluate the model
def evaluate_model(model, loader, device):
    model.eval()
    predictions = []
    labels = []
    probabilities = []
    correct = 0

    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            out = model(data)
            prob = F.softmax(out, dim=1)[:, 1]  # Probability of positive class
            pred = out.argmax(dim=1)

            predictions.extend(pred.cpu().numpy())
            labels.extend(data.y.cpu().numpy())
            probabilities.extend(prob.cpu().numpy())
            correct += pred.eq(data.y).sum().item()

    accuracy = correct / len(loader.dataset)
    f1 = f1_score(labels, predictions, average='binary')
    precision = precision_score(labels, predictions, average='binary')
    recall = recall_score(labels, predictions, average='binary')
    roc_auc = roc_auc_score(labels, probabilities)
    cm = confusion_matrix(labels, predictions)

    metrics = {
        "accuracy": accuracy,
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "roc_auc": roc_auc,
        "confusion_matrix": cm.tolist()  # Convert to list for JSON serialization
    }

    return metrics

# Main function to load and test the model
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load and test a trained HGCN model.")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the saved model file.")
    parser.add_argument("--test_data_path", type=str, required=True, help="Path to the test dataset file.")
    parser.add_argument("--in_channels", type=int, required=True, help="Number of input features for each node.")
    parser.add_argument("--hidden_channels", type=int, default=16, help="Number of hidden units in the model.")
    parser.add_argument("--out_channels", type=int, default=2, help="Number of output classes.")
    parser.add_argument("--device", type=str, default="cuda", help="Device to use for testing (default: cuda).")
    parser.add_argument("--metrics_output", type=str, default="hgcn_metrics.json", help="File to save evaluation metrics.")

    args = parser.parse_args()

    # Load the test dataset
    print(f"Loading test dataset from {args.test_data_path}...")
    test_data = torch.load(args.test_data_path)  # Assuming test dataset is saved as a PyTorch object
    test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

    # Initialize the model
    print("Initializing model...")
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = HGCN(in_channels=args.in_channels, hidden_channels=args.hidden_channels, out_channels=args.out_channels)
    model = model.to(device)

    # Load the model state dictionary
    print(f"Loading model from {args.model_path}...")
    model.load_state_dict(torch.load(args.model_path, map_location=device))

    # Evaluate the model
    print("Evaluating model...")
    metrics = evaluate_model(model, test_loader, device)

    # Print and save metrics
    print("\nEvaluation Metrics:")
    for key, value in metrics.items():
        if key != "confusion_matrix":
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}:\n{value}")

    # Save metrics to a JSON file
    with open(args.metrics_output, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to {args.metrics_output}")
