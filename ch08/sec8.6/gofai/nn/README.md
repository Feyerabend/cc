
## Neural Networks

The two files in this folder demonstrate the foundational mechanics of neural networks:
the learning rules that governed early connectionist models and the backpropagation
algorithm that revived the field in 1986. For the broader story of where neural networks
fit into the GOFAI period--the XOR crisis, the contrast with symbolic AI, the philosophical
debate--see the parent [README](../README.md) and the sibling folders
[`../xor/`](../xor/) and [`../lindstrom/`](../lindstrom/).


### Two Learning Rules

*Hebbian learning* (Hebb, 1949) is the older and biologically motivated rule. The principle
is simple: connections between units that are active simultaneously are strengthened. No
teacher, no error signal, no target output--the network reinforces co-occurrence. Elegant
and neurologically plausible, Hebbian learning is also weak on its own: without a correction
mechanism, it has no guarantee of producing useful behaviour.

The *delta rule* (Widrow and Hoff, 1960; also called the LMS or Widrow-Hoff rule) introduces
supervision. A teacher provides a target output, and the network adjusts weights in proportion
to the error between actual and desired output:

$$\Delta w_{yx} = \text{learning\_rate} \cdot (d_x - a_x) \cdot a_y$$

This is gradient descent on a quadratic error surface and is provably convergent when the
activation function is linear and the problem is linearly separable. Its limitation is also
its defining feature: it can only adjust weights into output units. There is no mechanism for
distributing error back through hidden layers--which is precisely what backpropagation adds.

*Backpropagation* (Rumelhart, Hinton & Williams, 1986) generalises the delta rule to
arbitrarily deep networks by propagating error gradients backward through the layers,
applying the chain rule at each step. This allows networks with hidden layers to learn
non-linear functions--including XOR, which defeated the single-layer perceptron. The
`nn.html` file demonstrates this interactively.


### `nn.py` -- Hebbian and Delta Learning

A Python implementation of both learning rules, built without external ML libraries.

*`Unit` class*: represents a single neuron with `id`, `activation`, `output`, and type
flags (`is_input`, `is_output`, `is_hidden`).

*`NeuralNetwork` class*: manages the network structure. Key methods:

- `add_unit()`, `add_connection()`: build the graph; connections store weights as
  `{(from_id, to_id): weight}`, initialised randomly if not provided.
- `set_input()`: sets activations on input units.
- `activate()`: propagates activation through hidden then output units, using either
  a *linear* function (sum of weighted inputs) or a *binary* step function (threshold).
- `train_hebbian()`: applies $\Delta w_{xy} = \text{lr} \cdot a_x \cdot a_y$ to all connections.
- `train_delta()`: applies the delta rule to weights into output units only.

The `__main__` block trains a simple AND gate using binary activation and the delta rule,
then illustrates Hebbian learning scenarios, printing weight evolution across epochs.


### `nn.html` -- Backpropagation Visualisation

An interactive browser demo of a multi-layer perceptron trained with backpropagation
and gradient descent.

*Architecture*: one input layer (2 nodes), one hidden layer (adjustable size), one output
layer (1 node). Sigmoid activation throughout; line thickness and colour (green/red)
show weight magnitude and sign.

*Training*: standard backpropagation--forward pass to compute output and MSE loss, then
backward pass distributing error through hidden layers via the chain rule, updating
`weightsHO` (hidden-to-output) and `weightsIH` (input-to-hidden).

*Datasets*: XOR, AND, and OR logic gates. XOR is the critical case--it requires the
hidden layer and cannot be solved by a single-layer network.

*Controls*: sliders for learning rate and hidden neuron count; buttons for start/stop,
single-epoch stepping, and network reset; a loss chart updated in real time.
