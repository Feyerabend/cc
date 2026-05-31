
## Optimisation

The book mentions SGD and its variants (Adam, RMSprop) in passing. This section
gives a self-contained treatment of the optimiser landscape: how each method works,
why the variants improve on plain SGD, and how they compare on a shared test problem.

### Files

| File                    | What it demonstrates                                       |
|-------------------------|------------------------------------------------------------|
| `optimisers.py`         | SGD, momentum, RMSprop, Adam implemented from scratch      |
| `compare_optimisers.py` | Side-by-side convergence on Rosenbrock and quadratic bowls |


### Key ideas extended here

*Momentum.* Plain SGD updates parameters using only the current gradient.
Momentum accumulates a velocity vector that smooths out the gradient signal
across iterations. This helps navigate narrow valleys in the loss surface where
the gradient oscillates across the valley but is small along it.

*RMSprop.* Introduced by Hinton in an unpublished Coursera lecture, RMSprop
maintains a per-parameter running average of squared gradients and divides each
update by the square root of this average. This adapts the learning rate
per-dimension, making it possible to use a larger global learning rate without
diverging on coordinates with large gradients.

*Adam.* Combines momentum (first moment) with RMSprop (second moment). The
first and second moment estimates are corrected for initialisation bias, since
both start at zero. Adam is the default optimiser in most modern deep learning
work. The update rule is:
$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t$$
$$v_t = \beta_2 v_{t-1} + (1 - \beta_2) g_t^2$$
$$\hat m_t = m_t / (1 - \beta_1^t), \quad \hat v_t = v_t / (1 - \beta_2^t)$$
$$\theta_t = \theta_{t-1} - \eta \hat m_t / (\sqrt{\hat v_t} + \epsilon)$$

*Learning rate schedules.* The learning rate $\eta$ is often decayed during
training. `optimisers.py` includes cosine annealing and step decay schedules
that can be wrapped around any base optimiser.
