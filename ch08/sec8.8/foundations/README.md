
## Foundations

This section extends the mathematical foundations from the part in the book.
There we introduced the forward pass and activation functions at a conceptual level.
Here we make those concrete by implementing them from scratch and visualising their
behaviour.

### Files

| File              | What it demonstrates                                         |
|-------------------|--------------------------------------------------------------|
| `forward_pass.py` | A minimal feedforward network, layer by layer                |
| `activations.py`  | ReLU, sigmoid, and tanh - values, derivatives, saturation    |
| `loss_surface.py` | How the loss landscape looks for a two-parameter toy problem |
| `forward_pass.c`  | The same forward pass in C, showing the raw arithmetic       |


### Key ideas extended here

*Dead neurons.* ReLU outputs exactly zero for any negative pre-activation. Once a
neuron is dead (its incoming weights push it permanently negative) gradient flow
through it stops entirely. `activations.py` plots this effect and compares it with
the leaky-ReLU variant that avoids it.

*Saturation and vanishing gradients.* Sigmoid and tanh both compress their inputs
into a bounded range. For large positive or negative inputs the derivative is nearly
zero, which causes gradients to shrink as they propagate backward through many layers.
The plots in `activations.py` make the saturation regions clearly visible.

*The loss surface.* For a network with two free parameters, `loss_surface.py`
draws the full loss landscape over a grid. This gives intuition for why gradient
descent can get trapped in flat regions or saddle points.
