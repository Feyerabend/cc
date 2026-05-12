
## Recurrent Neural Network (RNN)

Machine learning empowers systems to learn from data and improve performance over
time without explicit programming, and a specialised type of neural network, the
*Recurrent Neural Network* (RNN), is particularly adept at handling sequential data,
making it a cornerstone for tasks like natural language processing and time series
analysis.

*Recurrent Neural Networks* (RNNs) are a foundational class of artificial neural
networks specifically designed to model and recognise patterns in sequential data.
Typical applications include natural language processing (NLP), speech recognition,
and time series forecasting--domains where the order and context of inputs play
a crucial role.

Unlike traditional feedforward neural networks, which process inputs in isolation,
RNNs incorporate feedback connections that form directed cycles within the network.
This architectural feature allows RNNs to maintain a dynamic hidden state, a form
of internal memory that captures information about previous elements in the
sequence. As a result, RNNs can, at least in principle, learn temporal dependencies
and carry forward relevant context from one step to the next.

This temporal aspect makes RNNs particularly well-suited for tasks such as language
modeling, where the probability of a word appearing in a sentence depends on the
words that precede it. For example, given the phrase "The cat sat on the", a
well-trained RNN can leverage its memory to predict that the next word is likely
to be "mat".

However, traditional RNNs face significant challenges, including difficulty in
learning long-range dependencies due to issues like vanishing and exploding gradients
during training. These limitations led to the development of more advanced architectures
such as *Long Short-Term Memory* (LSTM) networks and Gated Recurrent Units (GRUs),
which introduce gating mechanisms to better manage information flow and maintain
relevant context over longer sequences.

In recent years, the landscape of sequence modeling has been transformed by the
emergence of transformer-based architectures, most notably *Large Language Models* (LLMs)
such as GPT. These models abandon recurrence entirely in favor of attention mechanisms,
which allow them to capture dependencies over arbitrary distances without the need
for sequential processing. As a result, LLMs have largely supplanted RNNs in many
high-profile NLP tasks, offering greater scalability, parallelisability, and performance.

Nonetheless, RNNs remain a conceptually important and historically significant approach
to sequence learning, and they continue to be useful in certain settings--particularly
when computational simplicity, online processing, or real-time constraints are factors.


### Mathematics

At each time step $t$, the vanilla RNN updates a hidden state $h_t$ from the previous
hidden state $h_{t-1}$ and the current input $x_t$:

```math
h_t = \tanh(W_{hh}\, h_{t-1} + W_{xh}\, x_t + b_h)
```

```math
y_t = \text{softmax}(W_{hy}\, h_t + b_y)
```

Training uses *Backpropagation Through Time* (BPTT): the loss $\mathcal{L} = \sum_t \mathcal{L}_t$
is accumulated across time steps and gradients flow backward through the unrolled graph.

*LSTM* replaces the single hidden state with a cell state $c_t$ and three gates:

```math
f_t = \sigma(W_f [h_{t-1}, x_t] + b_f), \quad
i_t = \sigma(W_i [h_{t-1}, x_t] + b_i)
```
```math
\tilde{c}_t = \tanh(W_c [h_{t-1}, x_t] + b_c), \quad
c_t = f_t \odot c_{t-1} + i_t \odot \tilde{c}_t
```
```math
o_t = \sigma(W_o [h_{t-1}, x_t] + b_o), \quad
h_t = o_t \odot \tanh(c_t)
```

*GRU* simplifies LSTM by merging the forget and input gates into an update gate $z_t$:

```math
z_t = \sigma(W_z [h_{t-1}, x_t]),\quad
r_t = \sigma(W_r [h_{t-1}, x_t])
```
```math
\tilde{h}_t = \tanh(W [r_t \odot h_{t-1}, x_t]),\quad
h_t = (1 - z_t) \odot h_{t-1} + z_t \odot \tilde{h}_t
```


### Gradient Challenges

The vanishing gradient problem arises during training when gradients become extremely
small as they are propagated backward through many time steps. For traditional RNNs,
the repeated application of the chain rule leads to the multiplication of many Jacobian
matrices. If these matrices contain values less than one in magnitude -- common with
sigmoid or tanh activations -- the gradients shrink exponentially. The network
effectively forgets earlier inputs, making it difficult to learn long-term dependencies.

Exploding gradients are the opposite failure: Jacobian values greater than one cause
gradients to grow exponentially, producing unstable updates. This is addressed with
gradient clipping.

LSTMs counteract vanishing gradients by using additive rather than multiplicative
cell-state updates. The additive path preserves gradient magnitude over many steps,
allowing effective learning even with distant context.


### Concepts

* *Hidden State:* A fixed-size vector summarising past inputs. Vanishes at sequence end; cannot
  grow with sequence length. Transformer attention has no such fixed bottleneck.
* *BPTT:* Unrolls the RNN across $T$ steps and applies standard backpropagation. Memory and
  compute scale with sequence length; truncated BPTT limits the unroll window.
* *LSTM vs. GRU:* Both mitigate vanishing gradients. LSTM has a separate cell state (more
  expressive); GRU is simpler and trains faster. Performance differences are task-dependent.
* *Character-Level vs. Word-Level:* Character-level models have tiny vocabularies but must
  learn spelling; word-level models need large embedding tables. Subword tokenisation
  (BPE, SentencePiece) is the modern compromise.
* *Teacher Forcing:* During training, ground-truth tokens are fed as inputs rather than the
  model's own predictions. Speeds convergence but can cause exposure bias at inference time.


### Samples


*Sample 1: Shakespeare Character-Level Generation*

* *Data:* Complete works of Shakespeare (~5 million characters).
* *Scenario:* A character-level RNN trains to predict the next character. After training, it
  generates stylistically plausible Shakespearean prose and verse, including iambic rhythms
  and stage directions, despite having no explicit grammatical knowledge.

*Sample 2: LSTM for Music Generation*

* *Data:* MIDI files encoded as sequences of note/duration tokens.
* *Scenario:* An LSTM learns chord progressions and melodic patterns. At inference time it
  autoregressively generates new melodies that follow the harmonic style of the training corpus,
  demonstrating LSTM's ability to capture long-range musical structure.

*Sample 3: GRU for Sensor Anomaly Detection*

* *Data:* Multivariate time series from industrial sensors (temperature, pressure, vibration).
* *Scenario:* A GRU trained on normal operating conditions is used for anomaly detection: a
  large reconstruction error on held-out windows signals equipment faults. GRU's lighter
  parameter count makes it practical for embedded deployment.
