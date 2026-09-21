"""Differentiable first-order Sugeno ANFIS and hierarchical composition."""

from __future__ import annotations

import copy
import itertools

import numpy as np
import torch
from torch import nn


class SugenoANFIS(nn.Module):
    """Grid-partition first-order Sugeno ANFIS with Gaussian membership functions."""

    def __init__(self, n_inputs: int, n_mfs: int = 2) -> None:
        super().__init__()
        self.n_inputs = n_inputs
        self.n_mfs = n_mfs
        centers = torch.linspace(0.25, 0.75, n_mfs).repeat(n_inputs, 1)
        self.centers = nn.Parameter(centers)
        self.log_sigmas = nn.Parameter(torch.full((n_inputs, n_mfs), np.log(0.25)))
        rules = list(itertools.product(range(n_mfs), repeat=n_inputs))
        self.register_buffer("rule_indices", torch.tensor(rules, dtype=torch.long))
        self.consequents = nn.Parameter(torch.zeros(len(rules), n_inputs + 1))
        nn.init.normal_(self.consequents, mean=0.0, std=0.05)

    @property
    def rule_count(self) -> int:
        return self.n_mfs ** self.n_inputs

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        sigma = torch.exp(self.log_sigmas).clamp_min(1e-3)
        memberships = torch.exp(-0.5 * ((x[:, :, None] - self.centers) / sigma) ** 2)
        selected = []
        for input_index in range(self.n_inputs):
            selected.append(memberships[:, input_index, self.rule_indices[:, input_index]])
        firing = torch.stack(selected, dim=-1).prod(dim=-1)
        weights = firing / firing.sum(dim=1, keepdim=True).clamp_min(1e-12)
        augmented_x = torch.cat([torch.ones((x.shape[0], 1), device=x.device), x], dim=1)
        rule_outputs = augmented_x @ self.consequents.T
        return (weights * rule_outputs).sum(dim=1)


def fit_anfis(
    model: SugenoANFIS,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    epochs: int = 300,
    learning_rate: float = 1e-2,
    patience: int = 40,
) -> dict[str, list[float] | float | int]:
    """Train with Adam and restore the epoch having the lowest validation MSE."""
    xtr = torch.as_tensor(x_train, dtype=torch.float32)
    ytr = torch.as_tensor(y_train, dtype=torch.float32)
    xva = torch.as_tensor(x_validation, dtype=torch.float32)
    yva = torch.as_tensor(y_validation, dtype=torch.float32)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    best_loss = float("inf")
    best_state = copy.deepcopy(model.state_dict())
    best_epoch = 0
    stale_epochs = 0
    history = {"training_loss": [], "validation_loss": []}

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        training_loss = torch.mean((model(xtr) - ytr) ** 2)
        training_loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            validation_loss = torch.mean((model(xva) - yva) ** 2).item()
        history["training_loss"].append(float(training_loss.item()))
        history["validation_loss"].append(validation_loss)

        if validation_loss < best_loss - 1e-8:
            best_loss = validation_loss
            best_epoch = epoch + 1
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    model.load_state_dict(best_state)
    history["best_validation_loss"] = best_loss
    history["best_epoch"] = best_epoch
    return history


def predict(model: SugenoANFIS, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        values = model(torch.as_tensor(x, dtype=torch.float32))
    return values.cpu().numpy()
