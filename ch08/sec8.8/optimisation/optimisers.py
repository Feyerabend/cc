"""
optimisers.py

Implements four common gradient-based optimisers from scratch:
  - SGD (vanilla)
  - SGD with momentum
  - RMSprop
  - Adam

Each optimiser follows the same interface:
    opt = Optimiser(params, ...)
    opt.step(grads)

where params and grads are dicts of the same shape mapping parameter
names to numpy arrays.

Also provides two learning rate schedules:
  - StepDecay: multiply lr by gamma every step_size steps
  - CosineAnnealing: lr follows a cosine curve from lr_max to lr_min
"""

import numpy as np


class SGD:
    def __init__(self, params, lr=0.01):
        self.params = {k: v.copy() for k, v in params.items()}
        self.lr = lr

    def step(self, grads):
        for k in self.params:
            self.params[k] -= self.lr * grads[k]


class SGDMomentum:
    def __init__(self, params, lr=0.01, momentum=0.9):
        self.params = {k: v.copy() for k, v in params.items()}
        self.lr = lr
        self.momentum = momentum
        self.velocity = {k: np.zeros_like(v) for k, v in params.items()}

    def step(self, grads):
        for k in self.params:
            self.velocity[k] = self.momentum * self.velocity[k] - self.lr * grads[k]
            self.params[k] += self.velocity[k]


class RMSprop:
    def __init__(self, params, lr=0.01, decay=0.99, eps=1e-8):
        self.params = {k: v.copy() for k, v in params.items()}
        self.lr = lr
        self.decay = decay
        self.eps = eps
        self.sq_avg = {k: np.zeros_like(v) for k, v in params.items()}

    def step(self, grads):
        for k in self.params:
            self.sq_avg[k] = self.decay * self.sq_avg[k] + (1 - self.decay) * grads[k] ** 2
            self.params[k] -= self.lr * grads[k] / (np.sqrt(self.sq_avg[k]) + self.eps)


class Adam:
    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.params = {k: v.copy() for k, v in params.items()}
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0

    def step(self, grads):
        self.t += 1
        for k in self.params:
            self.m[k] = self.beta1 * self.m[k] + (1 - self.beta1) * grads[k]
            self.v[k] = self.beta2 * self.v[k] + (1 - self.beta2) * grads[k] ** 2

            m_hat = self.m[k] / (1.0 - self.beta1 ** self.t)
            v_hat = self.v[k] / (1.0 - self.beta2 ** self.t)

            self.params[k] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class StepDecay:
    """Multiplies the optimiser's lr by gamma every step_size steps."""

    def __init__(self, optimiser, step_size=100, gamma=0.5):
        self.optimiser = optimiser
        self.step_size = step_size
        self.gamma = gamma
        self.base_lr = optimiser.lr
        self.iteration = 0

    def step(self, grads):
        self.optimiser.step(grads)
        self.iteration += 1
        if self.iteration % self.step_size == 0:
            self.optimiser.lr *= self.gamma

    @property
    def params(self):
        return self.optimiser.params


class CosineAnnealing:
    """Anneals lr from lr_max to lr_min following a cosine curve."""

    def __init__(self, optimiser, T_max, lr_min=0.0):
        self.optimiser = optimiser
        self.T_max = T_max
        self.lr_min = lr_min
        self.lr_max = optimiser.lr
        self.iteration = 0

    def step(self, grads):
        self.optimiser.lr = (
            self.lr_min
            + 0.5 * (self.lr_max - self.lr_min)
            * (1.0 + np.cos(np.pi * self.iteration / self.T_max))
        )
        self.optimiser.step(grads)
        self.iteration += 1

    @property
    def params(self):
        return self.optimiser.params
