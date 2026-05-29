
## Regularisation

The book mentions dropout regularisation and batch normalisation. This section
explains the mechanisms in more depth and provides clean implementations so their
behaviour during training and inference can be observed directly.


### Files

| File              | What it demonstrates                                     |
|-------------------|----------------------------------------------------------|
| `dropout.py`      | Dropout during training and inference - scale correction |
| `batch_norm.py`   | Batch normalisation forward pass, running statistics     |
| `weight_decay.py` | L2 regularisation equivalence with weight decay in SGD   |


### Key ideas extended here

*Dropout and the two-mode distinction.* During training, dropout randomly zeroes
activations with probability $p$ and scales the remaining ones by $1/(1-p)$.
During inference, dropout is disabled and all activations are used unchanged. This
inverted dropout convention means no scaling is needed at test time. Code that
forgets to set the model to eval mode will produce outputs that are systematically
smaller than expected--a common and subtle bug.

*Batch normalisation.* BatchNorm normalises each feature across the mini-batch,
then rescales with learned parameters $\gamma$ and $\beta$. During training the
mean and variance come from the current batch; during inference they are replaced
by exponential moving averages accumulated during training. BatchNorm acts as
both a regulariser and a smoothing effect on the loss surface, which is part of
why it accelerates training.

*L2 regularisation and weight decay.* Adding an $L_2$ penalty $\frac{\lambda}{2}\|\theta\|^2$
to the loss is equivalent to multiplying the weights by $(1 - \eta\lambda)$ before
the gradient step--which is why the technique is called *weight decay*. The two
formulations are mathematically equivalent for SGD but differ for adaptive
optimisers such as Adam, motivating the AdamW variant which applies weight decay
directly to the parameters rather than adding it to the gradient.
