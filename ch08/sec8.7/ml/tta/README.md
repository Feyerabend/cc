
> [!IMPORTANT]  
> The code requires (preferably) a virtual environment and torch installations.

## Test-Time Adaptation (TTA)

Test-Time Adaptation (TTA) is a technique for handling *distribution shift* -- the situation where
data encountered at deployment differs from training data. Standard models assume that training and
test data are drawn from the same distribution (i.i.d.). Real deployments violate this: lighting
changes, sensor noise, domain differences, or adversarial inputs all shift the distribution.

Instead of retraining when the input distribution changes, TTA adapts the model at inference time
on the specific input (or a small batch of inputs). This is especially useful for large pre-trained
models where full retraining is infeasible.

The code in `lm.py` implements a `CorrectionAwareTransformer` -- a Transformer Encoder with a
language model head and a confidence head. During inference, a TTA loss function fine-tunes the
model on the test input before prediction, improving robustness to corrupted or noisy text.

Another example of TTA on image data: [MNIST TTA](./../mnist/tta/).


### Mathematics

TTA minimises a combination of objectives computed on the test input $x$, updating model parameters
$\theta$ toward a better local fit:

*Entropy minimisation* -- reduces uncertainty in predictions:
```math
\mathcal{L}_{\text{ent}} = -\sum_k p_k(x;\theta) \log p_k(x;\theta)
```

*Consistency loss* -- predictions should be stable under small corruptions $\tilde{x}$:
```math
\mathcal{L}_{\text{con}} = \text{KL}(p(x;\theta) \| p(\tilde{x};\theta))
```

The combined TTA loss is:
```math
\mathcal{L}_{\text{TTA}} = \alpha\, \mathcal{L}_{\text{ent}} + \beta\, \mathcal{L}_{\text{con}} + \gamma\, \mathcal{L}_{\text{conf}}
```

where $\mathcal{L}_{\text{conf}}$ penalises low confidence scores on individual tokens. Parameters
are updated with a few AdamW steps before prediction is made.


### Concepts

* *Distribution Shift:* The gap between training distribution $p_{\text{train}}$ and deployment
  distribution $p_{\text{test}}$. Can arise from covariate shift (different inputs), label shift
  (different class frequencies), or concept drift (the relationship between input and label changes).
* *Adaptation Scope:* TTA can update all parameters, only final layers, or only normalisation layer
  statistics. Updating only BatchNorm/LayerNorm statistics (TTT-BN) is a common lightweight variant.
* *Online vs. Episodic:* Online TTA accumulates updates across the test stream; episodic TTA adapts
  independently per test sample using a fresh copy of the model.
* *Risk:* Unconstrained TTA can cause catastrophic forgetting or degrade performance if the test
  input is adversarial. Regularisation and limiting the number of adaptation steps mitigate this.


### Samples


*Sample 1: Corrupted Text Correction*

* *Scenario:* A Transformer language model encounters OCR errors ("teh", "hte") at deployment. TTA
  fine-tunes the model on the corrupted input using entropy and consistency losses before generation,
  improving output coherence without any labelled correction data.

*Sample 2: Medical Image Domain Shift*

* *Scenario:* A chest X-ray classifier trained on hospital A's scanner is deployed on hospital B's
  scanner, which has different exposure settings. TTA adapts the model's BatchNorm statistics at
  inference time on hospital B's images, recovering much of the accuracy lost from the domain shift.

*Sample 3: Autonomous Driving in Fog*

* *Scenario:* A driving perception model trained on clear-weather images encounters fog at deployment.
  Online TTA continuously updates the normalisation layers as foggy frames arrive, allowing the model
  to adapt its feature distributions to the altered visual conditions without requiring labelled foggy data.
