
## GAN

> [!IMPORTANT]
> This code requires TensorFlow, which must be installed for it to run. Additionally, it is recommended to
> use a computer with CUDA support or a compatible GPU, as training time will otherwise be significantly longer.

A *Generative Adversarial Network (GAN)* is a class of machine learning algorithms used to generate
new data similar to a training dataset. It consists of two neural networks: a *Generator* and a *Discriminator*,
trained simultaneously in a competitive setting.


### Mathematics

The Generator $G$ maps a random latent vector $z \sim p_z$ to a data sample, and the
Discriminator $D$ outputs the probability that a sample is real. They play a minimax game:

```math
\min_G \max_D \; \mathbb{E}_{x \sim p_{\text{data}}}[\log D(x)] + \mathbb{E}_{z \sim p_z}[\log(1 - D(G(z)))]
```

At equilibrium, $G$ produces samples indistinguishable from real data and $D$ outputs $\frac{1}{2}$
everywhere. In practice, the Wasserstein GAN variant replaces the cross-entropy loss with the
earth-mover distance, improving training stability:

```math
\min_G \max_{D \in \mathcal{D}} \; \mathbb{E}_{x}[D(x)] - \mathbb{E}_{z}[D(G(z))]
```

where $\mathcal{D}$ is the set of 1-Lipschitz functions enforced by weight clipping or a
gradient penalty.


### How GANs Work

1. *Generator*: Takes random noise (often a vector from a latent space) as input and generates fake data
   (e.g., images, audio). Its goal is to produce data that mimics the real training data distribution.

2. *Discriminator*: Evaluates whether a given input is real (from the training dataset) or fake (produced
   by the Generator). It outputs a probability score indicating the likelihood that the input is real.

3. *Adversarial Training*:
   - The Generator tries to "fool" the Discriminator by producing increasingly realistic data.
   - The Discriminator improves its ability to distinguish real data from fake.
   - This is a minimax game where the Generator minimises the Discriminator's ability to correctly classify
     fake data, while the Discriminator maximises its accuracy.
   - The loss function typically used is based on binary cross-entropy, though advanced GANs may use variants
     like Wasserstein loss for stability.


### Purpose of GANs

- *Data Generation*: Create realistic data, such as images, videos, or audio, that resemble the training
  set (e.g., generating realistic human faces, digits, or artwork).
- *Data Augmentation*: Generate synthetic data to supplement limited datasets, improving model training.
- *Creative Applications*: Enable artistic tasks like style transfer, image-to-image translation, or music generation.
- *Domain Adaptation*: Generate data for domains where real data is scarce or sensitive (e.g., medical imaging).


### StyleGAN-Inspired Implementation

The provided code implements a *StyleGAN-inspired GAN* for generating digit '7' images from the MNIST dataset.
Here's how it aligns with GAN principles:

1. *Generator Architecture*:
   - Uses a *mapping network* to transform random noise (latent vector) into a style vector, which controls the
     generation process.
   - Employs *Adaptive Instance Normalization (AdaIN)* to inject style information at multiple layers, allowing
     fine-grained control over generated image features.
   - Progressively upsamples from a learned constant (4x4) to the target resolution (28x28), incorporating style
     at each stage for high-quality outputs.
   - The use of a *truncation trick* (in `generate_images`) limits the variability of generated images to produce
     higher-quality, more stable outputs.

2. *Discriminator Architecture*:
   - Takes 28x28 grayscale images (MNIST digit 7) and outputs a real/fake score.
   - Includes *minibatch standard deviation* to prevent mode collapse by ensuring diversity in generated samples.
   - Uses progressive downsampling and normalisation to improve training stability.

3. *Training Process*:
   - The Generator and Discriminator are trained alternately using *Wasserstein loss* with *R1 regularization*
     (via `r1_penalty`) to stabilize training and prevent overfitting.
   - The Generator minimises the Discriminator’s ability to identify fake images, while the Discriminator maximises
     its ability to distinguish real MNIST digit 7 images from fake ones.
   - The training loop processes the dataset in batches, logs losses, and periodically saves generated images and
     model checkpoints.

4. *Specific Features*:
   - *Latent Space*: The latent dimension (`latent_dim=512`) provides a rich space for generating diverse images.
   - *Style Control*: The style vector (`style_dim=512`) and AdaIN allow control over image characteristics,
     inspired by StyleGAN’s approach for high-quality generation.
   - *MNIST Digit 7 Focus*: The code filters the MNIST dataset to train only on digit 7, specializing the model
     for this class.
   - *Checkpointing and Visualization*: Saves model checkpoints and generates image grids to monitor progress.


### Key Challenges Addressed

- *Training Stability*: Wasserstein loss and R1 regularisation mitigate issues like vanishing gradients or mode collapse.
- *Image Quality*: StyleGAN’s architecture (AdaIN, progressive growing) ensures high-fidelity outputs even for low-resolution
  (28x28) images.
- *Mode Collapse*: Minibatch standard deviation in the Discriminator encourages diversity in generated images.

In summary, GANs like this StyleGAN-inspired model are powerful tools for generating realistic data by pitting a Generator
against a Discriminator in a competitive training process. The purpose is to create new, high-quality data samples that
closely match the training distribution, with applications ranging from image synthesis to data augmentation.


### Samples


*Sample 1: Face Generation*

* *Training data:* Aligned celebrity face photographs (CelebA, FFHQ).
* *Scenario:* A StyleGAN trained on FFHQ generates photorealistic faces of people who do not exist,
  used in film production, game asset creation, and privacy-preserving dataset generation.

*Sample 2: Medical Image Augmentation*

* *Training data:* MRI scans labelled with tumour masks.
* *Scenario:* A GAN generates synthetic MRI images with and without tumours to augment a small
  annotated dataset. The synthetic images improve the downstream segmentation model's performance
  without exposing real patient data.

*Sample 3: Data-to-Image Synthesis*

* *Training data:* Paired satellite images and land-cover maps.
* *Scenario:* A conditional GAN (pix2pix) translates segmentation maps into realistic aerial
  photographs, enabling geographers to preview the visual appearance of planned land-use changes
  before they are built.

