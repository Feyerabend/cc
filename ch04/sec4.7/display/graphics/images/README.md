


### Images

Alongside text, graphics have always been central to how computers communicate with their
users. In the earliest systems, screens were limited to showing characters, but as technology
advanced, displays began to support images and geometric shapes. This shift marked a
transition from computers as tools for symbol manipulation to machines capable of rich
visual expression.

At the lowest level, computer graphics rely on the *pixel*, the smallest unit of a digital
display. An image is formed from a grid of pixels, each with a colour value that the screen
can illuminate. Early displays offered only black and white, then a handful of colours, but
modern screens can render millions of shades. Images stored as pixel data are called bitmaps
or raster graphics. They capture detail faithfully but do not scale well: enlarging a bitmap
often produces blocky, jagged results.

An alternative approach is *vector graphics*, which represent shapes using mathematical
descriptions of lines, curves, and fills rather than fixed pixels. Because vectors can be
scaled to any size without loss of quality, they are widely used in design, technical drawing,
and text rendering. The trade-off is that highly detailed or photographic images are
impractical to describe in vector form, so raster and vector methods often coexist.

Displaying graphics on computers also requires careful attention to rendering. The process of
converting stored image data into the correct pattern of pixels involves handling colour models
(such as RGB), scaling, anti-aliasing, and increasingly, hardware acceleration by graphics
processors (GPUs). Rendering ensures that an image or shape appears smoothly and consistently,
whether it is a photo, a window on the desktop, or a moving game character.

Beyond static images, computers also generate graphics dynamically. User interfaces rely on
drawing windows, icons, and controls; scientific applications display charts and simulations;
games and media produce immersive, animated environments. In each case, the computer must
combine geometry, colour, and timing into a coherent visual output.

The history of computer graphics is therefore one of constant expansion: from the simple dots
and lines of oscilloscopes and vector displays, to the colour bitmaps of early PCs, and now to
high-resolution, three-dimensional environments rendered in real time. Graphics, like text,
have become an essential medium through which computers both represent information and
engage human perception.




### 1. Pixels

At the most fundamental level, a digital image is composed of tiny discrete units
called *pixels*. Each pixel represents a single point in the image and carries
information about colour or intensity. When arranged in a grid, these pixels collectively
form a coherent image that can be displayed or printed. The density of this grid--often
expressed in pixels per inch (PPI)--determines how fine or coarse the image appears
to the human eye.

Pixels can store varying amounts of information depending on the bit depth of the image.
In an 8-bit grayscale image, each pixel holds a value between 0 and 255, representing
brightness from black to white. In a colour image, each pixel typically contains three
or four channels--for instance, red, green, blue (RGB), and optionally an alpha channel
(A) representing transparency. Together, these values define the visual characteristics
of the image.

#### Picos

While the Raspberry Pi Pico and its variants do not include a graphics subsystem like a GPU,
they are perfectly capable of managing pixel-level operations conceptually. In embedded systems,
controlling a small LCD or OLED display often involves writing pixel data directly to a
framebuffer or display buffer. The Pico's tight control over GPIO pins and SPI/I²C interfaces
makes it suitable for experimenting with low-level pixel manipulation. The Pico W and Pico 2W
further allow such displays to be networked or updated remotely.


### 2. Image Representation

A digital image is defined by its width and height--the number of pixels along the horizontal
and vertical axes--and by the number of channels per pixel. Grayscale images use a single
channel, while RGB and RGBA images use three or four. The *bit depth* per channel determines
how finely each channel's value can vary, influencing both dynamic range and file size.

Images can also use *indexed colour* representation, where pixels contain indices into a
palette rather than full colour values. This approach was common in early computer graphics
to reduce memory usage. Modern image formats typically store full RGB data, but indexed
formats remain relevant in constrained environments or for stylistic purposes such as
retro game design.

#### Picos

On the Pico, image representation is a practical concern when working with limited memory.
A full-colour bitmap at VGA resolution would exceed the available RAM, but indexed or 
educed-resolution formats are manageable. The Pico's microcontroller design encourages
thinking about efficient representations--for example, storing sprites as 1-bit masks or using
16-bit RGB565 format. With the wireless models (Pico W and Pico 2W), such images can
also be transmitted to or from a networked device, making compact representation essential.



### 3. Colour Models and Spaces

Colour models describe how colours are represented numerically. The RGB model is *additive*,
combining red, green, and blue light to produce other colours; it underlies most displays. CMYK,
in contrast, is *subtractive*, using cyan, magenta, yellow, and black inks in printing. HSV
(Hue, Saturation, Value) and HSL (Hue, Saturation, Lightness) are more perceptually intuitive,
separating chromatic information from brightness. Grayscale images use a single channel for
luminance, while models like YUV or Y'CbCr separate brightness from colour for compression
efficiency in video. The CIELAB model attempts perceptual uniformity, so numeric differences
correspond to perceived colour differences.

Understanding colour spaces is crucial when converting between devices or preparing images for
processing. Each model serves a specific context, balancing fidelity, computational efficiency
and perceptual relevance.

#### Picos

For the Pico family, colour models become relevant in applications involving small displays or
LED matrices. RGB values often need to be translated into device-specific formats, such as 5-6-5
bit encoding for TFT screens or PWM duty cycles for LEDs. While the base Pico provides direct
control, the Pico W can facilitate remote adjustments of colour parameters via Wi-Fi, and the
Pico 2's increased speed allows for real-time colour transitions or gradient computations.



### 4. Image File Formats

Image data must be stored in files that encode both pixel information and metadata. Common formats
differ by compression, colour depth, and intended use. BMP is a simple, uncompressed format, mainly
used for raw experimentation. PNG provides lossless compression and supports transparency, making
it ideal for interface graphics. JPEG uses lossy compression optimised for photographs, trading exact
accuracy for reduced size. GIF relies on indexed colour and can store short animations. TIFF
remains a flexible format for professional workflows, while RAW captures unprocessed sensor data
directly from cameras. Simpler formats like PNM or PAM are used in research and teaching due to
their plain-text structure.

Each format embodies trade-offs between simplicity, quality, and efficiency--an essential concept in
digital imaging.

#### Picos

File formats are conceptually important for Pico-based systems because storage and transmission constraints
often dictate format choice. A Pico project using a small external flash or SD card may store icons as
raw bitmaps, while a Pico W could receive compressed PNG or JPEG data from a network. With the Pico 2
and 2W, faster cores and larger memory allow limited decoding of compressed images directly on the
device--a key conceptual step toward lightweight embedded image viewers.



### 5. Image Manipulations

Image manipulation encompasses operations that modify pixel data to enhance or transform the image.
*Geometric operations* include scaling, rotation, cropping, and mirroring, which alter spatial relationships.
*Point operations* adjust brightness, contrast, or gamma correction by applying mathematical functions to
each pixel independently. *Colour operations* involve conversions between spaces, palette adjustments,
or transformations like converting RGB to grayscale.

Such operations serve both aesthetic and functional goals, from preparing images for machine learning
to improving visual clarity for human observers.

#### Picos

Conceptually, the Pico's control over data streams mirrors the principles of image manipulation. For instance,
adjusting the brightness of an LED matrix or TFT display parallels per-pixel operations. Although the Pico
cannot handle large images in RAM, it can perform these operations on small buffers or streams in real time.
The Pico 2's dual-core capability enables parallel processing of pixel data, and the wireless variants
(Pico W, Pico 2W) can apply remote or cloud-sent image manipulations, illustrating embedded distributed graphics.



### 6. Filters and Convolution

Filtering is a central idea in image processing. A *convolution filter* modifies each pixel based on its
neighbours using a mathematical kernel. Simple averaging produces blurring, Gaussian kernels yield smooth blurs,
and derivative-based kernels such as Sobel or Laplacian detect edges. Sharpening enhances contrast at
boundaries, while median filtering reduces noise without blurring edges.

Conceptually, these filters act as local transformations that reveal structural information used in vision,
graphics, and machine perception.

#### Picos

Although heavy convolutional filtering is beyond the computational scope of most microcontrollers, the concept
is deeply instructive. A Pico can implement small 3x3 kernels in real time for simple effects on low-resolution
displays or sensors. The Pico 2's faster processor allows exploring such algorithms conceptually, while the
Pico W and Pico 2W could stream sensor or image data to and from more capable devices performing convolution
externally. This distributed processing model reflects real-world IoT image systems.



### 7. Higher-Level Techniques

Beyond basic filtering, higher-level image operations include *morphological transformations* (erosion and dilation),
*Fourier transforms* (for frequency domain analysis), and *compression* (lossless and lossy). Morphological operations
treat images as sets, modifying shapes and boundaries--useful in segmentation. The Fourier transform decomposes
images into sinusoidal components, revealing patterns in frequency space, fundamental to compression and signal
analysis. Downsampling and mipmaps reduce resolution while preserving detail, crucial in graphics and computer vision.

These methods show how complex processing builds from simpler pixel and filter operations.

#### Picos

While the Pico cannot handle full-size Fourier transforms efficiently, the conceptual parallels are rich. For instance,
understanding frequency decomposition aids in designing PWM-driven signals or interpreting sensor oscillations--both
common in embedded systems. The Pico 2's computational gains open possibilities for small-scale FFT experiments,
and wireless models could relay frequency-domain data to cloud analytics services.



### 8. Raster vs Vector

Raster graphics represent images as arrays of pixels, inherently resolution-dependent. Zooming in reveals pixel boundaries.
Vector graphics, by contrast, describe images through shapes, lines, and curves--scalable without loss. Each approach has
advantages: raster for photographs and texture detail, vector for logos and diagrams. Converting between them requires
interpolation or tessellation.

Conceptually, the distinction illustrates the trade-off between data volume and abstraction--raster for immediacy,
vector for generality.

#### Picos

On the Pico, raster and vector concepts appear in display handling. A framebuffer display is raster-based, while rendering
geometric primitives or fonts approximates vector operations. Understanding these paradigms conceptually helps when designing
efficient rendering routines or font systems for limited displays. The Pico 2's speed supports rudimentary vector drawing
(lines, polygons), while the Pico W's connectivity allows vector data streaming from external systems.



### 9. Code Snippets (Conceptual)

Conceptual code snippets illustrate algorithmic thinking in image processing. For example, adjusting brightness can be done
by adding a constant value to each channel, while convolution applies a sliding window to compute weighted sums. These
snippets embody the algorithmic essence of image manipulation, even if simplified.

They emphasise that images are simply structured numerical data--accessible to general computation principles.

#### Picos

Such code-level thinking applies directly to the Pico's environment, where data manipulation is constrained but precise.
Writing loops to update pixel data, apply brightness scaling, or manage buffers is analogous to embedded control code.
The Pico 2's dual-core architecture even allows pipeline-style processing--one core handling data input, another performing
transformation--mirroring how larger systems process images.



### 10. Applications

Image processing finds applications in photography, computer vision, scientific visualisation, and machine learning. In
photography, manipulation enhances quality or corrects defects. In medical and satellite imaging, precision is crucial
for interpretation. Computer vision uses image processing for feature extraction and object recognition. Machine learning
pipelines often rely on preprocessing to normalise, augment, or filter data for models.

These applications show how low-level pixel operations scale into major technological domains.

#### Picos

Conceptually, the Pico family embodies the embedded frontier of imaging. A Pico W can act as a remote sensor node transmitting
frames, while a Pico 2 can handle on-device preprocessing--thresholding, edge detection, or signal analysis--before sending
results. The family as a whole represents how ideas from large-scale imaging can be distilled into compact, efficient embedded
computation, very useful for educational and experimental use.


