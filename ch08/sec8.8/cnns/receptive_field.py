"""
receptive_field.py

Computes the receptive field size after each layer in a convolutional
network. The receptive field at layer l is the region in the original
input that influences a single output neuron at that layer.

For a stack of convolutional layers with kernel sizes k_l and strides s_l,
the receptive field grows as:

    RF_l = RF_{l-1} + (k_l - 1) * prod_{i=1}^{l-1} s_i

This is the formula for dilated convolutions with dilation=1.

We compute and print the receptive field for three toy architectures:
  1. All-3x3 stack with stride 1 (VGG-style)
  2. All-3x3 stack with occasional stride-2 layers (ResNet-style)
  3. Mix of 1x1 and 3x3 layers (bottleneck-style)

Understanding receptive field growth is essential for choosing
architecture depth and kernel sizes for a given spatial task.
"""


def compute_receptive_field(layers):
    """
    Parameters
    ----------
    layers : list of (kernel_size, stride) tuples

    Returns
    -------
    rf_per_layer : list of int
        Receptive field at the output of each layer.
    """
    rf = 1
    cumulative_stride = 1
    rf_per_layer = []

    for k, s in layers:
        rf = rf + (k - 1) * cumulative_stride
        cumulative_stride *= s
        rf_per_layer.append(rf)

    return rf_per_layer


def print_rf_table(name, layers):
    rfs = compute_receptive_field(layers)
    print(f"\n{name}")
    print(f"{'Layer':>6}  {'Kernel':>7}  {'Stride':>7}  {'RF':>6}")
    print("  " + "-" * 30)
    for l, ((k, s), rf) in enumerate(zip(layers, rfs), start=1):
        print(f"  {l:>4}   {k:>6}   {s:>6}   {rf:>6}")


def main():
    vgg_style = [(3, 1)] * 8
    print_rf_table("VGG-style: eight 3x3 conv layers, stride=1", vgg_style)

    resnet_style = [
        (3, 1), (3, 1),
        (3, 2), (3, 1), (3, 1),
        (3, 2), (3, 1), (3, 1),
        (3, 2), (3, 1), (3, 1),
    ]
    print_rf_table("ResNet-style: stride-2 layers at layers 3, 6, 9", resnet_style)

    bottleneck = [
        (1, 1), (3, 1), (1, 1),
        (1, 1), (3, 2), (1, 1),
        (1, 1), (3, 1), (1, 1),
    ]
    print_rf_table("Bottleneck: 1x1, 3x3, 1x1 repeated (with one stride-2)", bottleneck)

    print("\nNote: a larger receptive field means each output neuron")
    print("integrates information from a wider region of the input.")
    print("Stride-2 layers expand the RF rapidly at the cost of")
    print("spatial resolution in the feature map.")


if __name__ == "__main__":
    main()
