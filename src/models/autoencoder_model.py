"""
Deep Learning Autoencoder for Unsupervised/Semi-Supervised Anomaly Detection.
Trained strictly on normal network traffic flows (label == 0) to learn normal representations.
Anomalies and cyber attacks are detected when the reconstruction error (MSE) exceeds
a calibrated threshold.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from src.config import config

logger = logging.getLogger(__name__)

# Set reproducible seeds
torch.manual_seed(config.RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(config.RANDOM_SEED)

class AutoencoderNetwork(nn.Module):
    """
    Symmetric Deep Autoencoder neural network with bottleneck latent space.
    """
    def __init__(self, input_dim: int, hidden_dims: Tuple[int, ...] = (64, 32, 16)):
        super().__init__()
        self.input_dim = input_dim

        # Encoder: D -> 64 -> 32 -> 16
        encoder_layers = []
        in_dim = input_dim
        for h_dim in hidden_dims:
            encoder_layers.append(nn.Linear(in_dim, h_dim))
            encoder_layers.append(nn.BatchNorm1d(h_dim))
            encoder_layers.append(nn.LeakyReLU(negative_slope=0.1))
            in_dim = h_dim
        self.encoder = nn.Sequential(*encoder_layers)

        # Decoder: 16 -> 32 -> 64 -> D
        decoder_layers = []
        rev_dims = list(reversed(hidden_dims[:-1])) + [input_dim]
        in_dim = hidden_dims[-1]
        for i, h_dim in enumerate(rev_dims):
            decoder_layers.append(nn.Linear(in_dim, h_dim))
            if i < len(rev_dims) - 1:
                decoder_layers.append(nn.BatchNorm1d(h_dim))
                decoder_layers.append(nn.LeakyReLU(negative_slope=0.1))
            in_dim = h_dim
        self.decoder = nn.Sequential(*decoder_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

class DeepAutoencoderModel:
    """
    Wrapper around AutoencoderNetwork managing training on normal traffic,
    anomaly score computation, threshold calibration, and inference.
    """

    def __init__(
        self,
        input_dim: Optional[int] = None,
        hidden_dims: Tuple[int, ...] = config.AE_HIDDEN_DIMS,
        learning_rate: float = config.AE_LEARNING_RATE,
        batch_size: int = config.AE_BATCH_SIZE,
        epochs: int = config.AE_EPOCHS,
        weight_decay: float = config.AE_WEIGHT_DECAY,
        threshold_percentile: float = config.AE_THRESHOLD_PERCENTILE,
        device: Optional[str] = None
    ):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.weight_decay = weight_decay
        self.threshold_percentile = threshold_percentile

        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.network: Optional[AutoencoderNetwork] = None
        self.threshold: float = 0.0
        self.loss_history: List[float] = []
        self.is_trained: bool = False

    def _init_network(self, input_dim: int):
        self.input_dim = input_dim
        self.network = AutoencoderNetwork(input_dim=input_dim, hidden_dims=self.hidden_dims).to(self.device)

    def fit(
        self,
        X_train_normal: np.ndarray,
        X_val_normal: Optional[np.ndarray] = None
    ) -> "DeepAutoencoderModel":
        """
        Train the autoencoder EXCLUSIVELY on normal traffic flows (label == 0).
        Calibrates the anomaly threshold on normal reconstruction errors.
        """
        if self.network is None or self.input_dim != X_train_normal.shape[1]:
            self._init_network(X_train_normal.shape[1])

        logger.info(
            f"Training Autoencoder on {len(X_train_normal):,} NORMAL samples "
            f"(features={self.input_dim}, device={self.device}, epochs={self.epochs})..."
        )

        tensor_train = torch.tensor(X_train_normal, dtype=torch.float32)
        dataset = TensorDataset(tensor_train)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, drop_last=len(dataset) > self.batch_size)

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(
            self.network.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )

        self.loss_history = []
        self.network.train()

        for epoch in range(1, self.epochs + 1):
            epoch_loss = 0.0
            for batch in loader:
                x_batch = batch[0].to(self.device)
                optimizer.zero_grad()
                reconstructed = self.network(x_batch)
                loss = criterion(reconstructed, x_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * len(x_batch)

            avg_loss = epoch_loss / len(dataset)
            self.loss_history.append(avg_loss)
            if epoch % 5 == 0 or epoch == 1 or epoch == self.epochs:
                logger.info(f"Epoch [{epoch:02d}/{self.epochs:02d}] - Reconstruction MSE: {avg_loss:.6f}")

        # Calibrate anomaly threshold on normal validation or training samples
        val_samples = X_val_normal if X_val_normal is not None else X_train_normal
        normal_errors = self.compute_reconstruction_error(val_samples)
        self.threshold = float(np.percentile(normal_errors, self.threshold_percentile))
        self.is_trained = True

        logger.info(
            f"Autoencoder training complete. Calibrated threshold ({self.threshold_percentile}th percentile): {self.threshold:.6f}"
        )
        return self

    def compute_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """
        Computes per-sample Mean Squared Error (MSE) between input and decoded output.
        High error indicates deviation from normal traffic (anomaly/attack).
        """
        if not self.is_trained and self.network is None:
            raise ValueError("Autoencoder is not initialized or trained.")

        self.network.eval()
        tensor_data = torch.tensor(X, dtype=torch.float32)
        loader = DataLoader(TensorDataset(tensor_data), batch_size=256, shuffle=False)

        errors = []
        with torch.no_grad():
            for batch in loader:
                x_b = batch[0].to(self.device)
                recon = self.network(x_b)
                # Compute sample-wise MSE: mean squared error across all features
                batch_mse = torch.mean((recon - x_b) ** 2, dim=1).cpu().numpy()
                errors.extend(batch_mse)

        return np.array(errors, dtype=np.float32)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict binary labels: 1 (Attack/Anomaly) if reconstruction error > threshold, else 0 (Normal).
        """
        errors = self.compute_reconstruction_error(X)
        return (errors > self.threshold).astype(int)

    def predict_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Return continuous anomaly scores (reconstruction MSE).
        Higher values indicate stronger anomaly severity.
        """
        return self.compute_reconstruction_error(X)

    def save(self, model_path: Optional[str] = None, config_path: Optional[str] = None):
        """Save PyTorch weights and configuration parameters."""
        model_path = model_path or config.AUTOENCODER_PATH
        config_path = config_path or config.AE_CONFIG_PATH

        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.save(self.network.state_dict(), model_path)

        metadata = {
            "input_dim": self.input_dim,
            "hidden_dims": list(self.hidden_dims),
            "threshold": self.threshold,
            "threshold_percentile": self.threshold_percentile,
            "loss_history": self.loss_history,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate
        }
        with open(config_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Autoencoder saved to: {model_path} and config to: {config_path}")

    @classmethod
    def load(cls, model_path: Optional[str] = None, config_path: Optional[str] = None) -> "DeepAutoencoderModel":
        """Load trained Autoencoder from disk."""
        model_path = model_path or config.AUTOENCODER_PATH
        config_path = config_path or config.AE_CONFIG_PATH

        if not os.path.exists(model_path) or not os.path.exists(config_path):
            raise FileNotFoundError(f"Autoencoder files missing ({model_path} or {config_path}).")

        with open(config_path, "r") as f:
            meta = json.load(f)

        instance = cls(
            input_dim=meta["input_dim"],
            hidden_dims=tuple(meta["hidden_dims"]),
            threshold_percentile=meta["threshold_percentile"],
            epochs=meta["epochs"],
            batch_size=meta["batch_size"],
            learning_rate=meta["learning_rate"]
        )
        instance._init_network(meta["input_dim"])
        instance.network.load_state_dict(torch.load(model_path, map_location=instance.device))
        instance.threshold = float(meta["threshold"])
        instance.loss_history = meta.get("loss_history", [])
        instance.is_trained = True
        logger.info(f"Autoencoder loaded from {model_path} (threshold={instance.threshold:.6f})")
        return instance
