import torch
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
import json
import argparse
from torch_geometric.data import Data

# Define the GCN model structure
class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GCN, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.fc = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        x = global_mean_pool(x, batch)  # Aggregates node embeddings into graph embeddings
        x = self.fc(x)
        return F.log_softmax(x, dim=1)

# Function to evaluate the model
def evaluate_model(model, loader):
    model.eval()
    correct = 0
    total = 0
    all_predictions = []
    all_labels = []
    all_probabilities = []

    with torch.no_grad():
        for data in loader:
            out = model(data)
            prob = F.softmax(out, dim=1)[:, 1]  # Probability of class 1
            pred = out.argmax(dim=1)

            correct += (pred == data.y).sum().item()
            total += data.y.size(0)

            all_predictions.extend(pred.tolist())
            all_labels.extend(data.y.tolist())
            all_probabilities.extend(prob.tolist())

    accuracy = correct / total if total > 0 else 0
    roc_auc = roc_auc_score(all_labels, all_probabilities) if len(set(all_labels)) > 1 else float('nan')
    f1 = f1_score(all_labels, all_predictions, average='binary')
    precision = precision_score(all_labels, all_predictions, average='binary')
    recall = recall_score(all_labels, all_predictions, average='binary')
    cm = confusion_matrix(all_labels, all_predictions)

    metrics = {
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm.tolist()  # Convert to list for JSON serialization
    }

    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC AUC: {roc_auc:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"Confusion Matrix:\n{cm}")

    return metrics

# Main function to load and test the model
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Load and test a trained GCN model.")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the saved model file.")
    parser.add_argument("--test_data_path", type=str, required=True, help="Path to the test dataset file.")
    parser.add_argument("--in_channels", type=int, required=True, help="Number of input features for each node.")
    parser.add_argument("--hidden_channels", type=int, default=16, help="Number of hidden units in GCN.")
    parser.add_argument("--out_channels", type=int, default=2, help="Number of output classes.")
    parser.add_argument("--metrics_output", type=str, default="metrics.json", help="File to save the evaluation metrics.")

    args = parser.parse_args()

    # Load the test dataset
    print(f"Loading test dataset from {args.test_data_path}...")
    test_data = torch.load(args.test_data_path)  # Assuming the test dataset is saved as a PyTorch object
    test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

    # Initialize the model
    print("Initializing model...")
    model = GCN(in_channels=args.in_channels, hidden_channels=args.hidden_channels, out_channels=args.out_channels)

    # Load the model state dictionary
    print(f"Loading model from {args.model_path}...")
    model.load_state_dict(torch.load(args.model_path))

    # Evaluate the model
    print("Evaluating model...")
    metrics = evaluate_model(model, test_loader)

    # Save metrics to a file
    with open(args.metrics_output, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to {args.metrics_output}")
