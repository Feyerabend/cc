
## Deep Learning: Supplementary Material

This folder accompanies the *Deep Learning* part of the book. It extends the
theoretical content with runnable code, worked examples, and additional explanations
that go beyond the introductory text.

Each subfolder corresponds to a section of the chapter and is self-contained.

### Structure

| Folder                               | Topic                                                  |
|--------------------------------------|--------------------------------------------------------|
| [foundations/](./foundations/)       | Activation functions, forward pass, loss surfaces      |
| [cnns/](./cnns/)                     | Convolution arithmetic, receptive fields, feature maps |
| [rnns_lstms/](./rnns_lstms/)         | Vanishing gradients, LSTM cell implementation          |
| [transformers/](./transformers/)     | Self-attention from scratch, positional encoding       |
| [optimisation/](./optimisation/)     | SGD, momentum, Adam -- a comparative walkthrough       |
| [regularisation/](./regularisation/) | Dropout, weight decay, batch normalisation             |


### Requirements

```
numpy >= 1.24
matplotlib >= 3.7
```

All examples are written in Python (NumPy only, no deep learning framework) unless
otherwise noted. A few low-level illustrations are written in C to make the
arithmetic explicit. Each C file compiles with a plain `gcc` invocation shown in
the file header.


### Running the Python examples

```bash
pip install numpy matplotlib
python foundations/forward_pass.py
```

### Reference

* Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep learning*. MIT Press.

![Deep Learning](./../assets/image/deep.jpeg)

