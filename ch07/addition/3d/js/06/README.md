
## There’s more than one way to bake a cake: Clifford Algebra and Matrix Operations

A recurring observation in programming, which I frequently revisit, is the sheer diversity
of approaches available to achieve an identical outcome. Programmers, with their individual
preferences and problem-solving styles, often embark on distinct computational paths that
ultimately converge on the same result, forming a kind of equivalence class in terms of their
output. This phenomenon is vividly illustrated in the comparison below, where two fundamentally
different mathematical paradigms for 3D rotation--Clifford algebra and traditional matrix
operations--yield strikingly similar visual representations of a rotating cube.

While a discerning eye can certainly perceive subtle differences, particularly in the initial
smoothness or long-term stability of the rotations, the fact that one method appears "faster"
or more robust often stems from external factors rather than inherent mathematical superiority.
Matrix operations, for instance, boast a long and rich history within computer graphics,
leading to extensive hardware acceleration, highly optimised libraries, and well-established
best practices for numerical stability. This mature ecosystem has refined their performance
and predictability over decades. In contrast, the application of geometric or Clifford algebra
to real-time 3D graphics, while theoretically elegant and offering profound mathematical insights
into geometric transformations, remains somewhat more experimental in practical programming
contexts. It's an area of ongoing research and development, meaning that its implementations may
not yet benefit from the same level of optimisation, hardware support, or widespread adoption
as traditional matrix-based methods. Therefore, any perceived performance discrepancy often
reflects the current state of technological maturity and community adoption rather than an
intrinsic limitation of the mathematical framework itself. Both approaches ultimately demonstrate
the compelling idea that diverse mathematical formulations can beautifully describe and
manipulate the same underlying geometric realities.

The fundamental difference between the two files, `cliffhanger.html` and `cliffhanger2.html`, lies
in the mathematical functions used within the `CliffordBivector` class to convert a bivector into a
rotor. Specifically, `cliffhanger.html` employs Taylor series approximations for cosine and sine
when calculating `cosHalf` and `sinHalf` in its `toRotor` method. In contrast, `cliffhanger2.html`
utilizes the standard `Math.cos()` and `Math.sin()` functions for these calculations, resulting
in more accurate trigonometric values. This seemingly minor alteration has a significant impact
on the Clifford algebra-based cube's rotation, as the approximations in `cliffhanger.html` lead
to drift and instability over time, causing the cube to deform or behave erratically compared to
the smooth and consistent rotation achieved in `cliffhanger2.html` due to precise trigonometric
functions. Another subtle difference is the `time` increment in the `animate` function, where
`cliffhanger.html` uses `0.02` while `cliffhanger2.html` uses `0.01`, meaning the latter rotates
the cube at half the speed of the former.

Now, to delve deeper into the concepts of geometric/Clifford algebra and ordinary matrix operations
in regard to 3D rotations, it's essential to understand their underlying principles.

Ordinary matrix operations, as seen in the `MatrixRotation` class in both files, represent rotation
by applying a 3x3 transformation matrix to a 3D vector. Each element in the matrix is a scalar,
and the multiplication of the matrix by a vector results in a new vector whose components are linear
combinations of the original vector's components. To achieve a composite rotation, such as a
rotation around X, then Y, then Z, matrices are multiplied together in a specific order. This
sequential multiplication can sometimes lead to issues like "gimbal lock" in more complex systems,
where degrees of freedom are lost, making certain rotations impossible. While matrix multiplication
is well-understood and widely used in computer graphics due to hardware optimisation, it can be less
intuitive for representing the physical nature of rotations. Each axis of rotation is treated
somewhat independently, and combining them requires a defined sequence of operations.

Geometric algebra, or Clifford algebra, offers an alternative and often more unified approach to
describing geometric transformations like rotations. In this framework, vectors are not just lists
of coordinates; they are elements of a larger algebraic structure that includes scalars, bivectors,
and trivectors (or pseudovectors in 3D). Rotations in geometric algebra are performed using "rotors."
A rotor is an element of the algebra that represents a rotation by sandwiching the object being
rotated between the rotor and its reverse. Specifically, a bivector, which represents a plane of
rotation and an associated magnitude of rotation, is used to construct a rotor. For example, in 3D
Euclidean space, a bivector like `xy` represents a rotation in the XY-plane. The `toRotor()` method
in the `CliffordBivector` class demonstrates this, transforming the bivector components (xy, xz, yz)
into a rotor that is mathematically equivalent to a quaternion.

The key advantage of geometric algebra for rotations lies in its direct representation of planes of
rotation and its ability to combine rotations in a way that avoids gimbal lock. Instead of a sequence
of single-axis rotations, a single bivector can represent a rotation around an arbitrary axis by
specifying its components in the different planes (e.g., xy, xz, yz). The rotor then intrinsically
carries all the information needed for the rotation, including the axis and angle. When combining
rotations, rotors can be directly multiplied, and the result is another rotor that represents the
combined transformation, regardless of the order of individual axis rotations. This provides a more
robust and often more elegant mathematical description of rotations, although its implementation
in computational systems can sometimes be less straightforward than traditional matrix algebra,
especially when highly optimised matrix libraries are available. The difference in the stability of
the rotating cube between `cliffhanger.html` and `cliffhanger2.html` highlights the importance of
numerical precision even in these more abstract algebraic systems; inaccurate approximations of
fundamental trigonometric functions can undermine the inherent stability benefits of the geometric
algebra approach.


