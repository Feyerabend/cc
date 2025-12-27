
## Kalman filter

A Kalman filter is a recursive algorithm for estimating the internal state
of a linear dynamic system based on noisy measurements. It uses a two-stage
process that first predicts the state and then updates that prediction with
new measurements. The state transition model is given by $x_k = A x_{k-1} + B u_k + w_k$,
where $A$ is the state transition matrix, $B$ is the control input matrix,
$u_k$ is the control input, and $w_k$ represents process noise, assumed
to be Gaussian with covariance $Q$. The measurement model is expressed as
$z_k = H x_k + v_k$, where $H$ is the observation matrix and $v_k$
is the measurement noise with covariance $R$.

In the prediction phase, the filter computes the predicted state
x̂ₖ⁻ = A x̂ₖ₋₁ + B uₖ
and the corresponding predicted covariance
$P_k^{-} = A P_{k-1} A^T + Q$. When a new measurement $z_k$ is received,
the filter calculates the Kalman gain $K_k = P_k^{-} H^T (H P_k^{-} H^T + R)^{-1}$
to determine how much weight should be given to the measurement compared to the prediction.
The state estimate is then updated to
x̂ₖ = x̂ₖ⁻ + Kₖ (zₖ − H x̂ₖ⁻)
and the covariance is revised to $P_k = (I - K_k H) P_k^{-}$.

The filter's efficiency and optimality stem from the assumption that both the process
noise and the measurement noise are Gaussian, ensuring that the posterior state estimate
remains Gaussian. This results in a minimum mean squared error estimate under linear
conditions. Extensions such as the *Extended Kalman Filter* (EKF) and the
*Unscented Kalman Filter* (UKF) adapt the basic principles to handle nonlinear systems,
either by linearising around the current estimate or by employing deterministic sampling
techniques.

The algorithm continuously refines its estimate by combining the predicted state
with new measurements, striking a balance that evolves with each update.


### Example

Here's a simple example of using a Kalman filter in MicroPython to *smooth out* a list of
temperature measurements. This can help reduce noise in the measurements, providing a more
stable temperature reading.

The *Kalman filter* is an iterative algorithm that estimates the true value of a variable
(like temperature) by considering both the measurement and the estimated previous state.
It's widely used in embedded systems for filtering noisy sensor data.


### Temperature readings in MicroPython

```python
class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, estimated_error, initial_value=0):
        self.process_variance = process_variance  # process noise
        self.measurement_variance = measurement_variance  # measurement noise
        self.estimated_error = estimated_error  # initial estimated error
        self.value = initial_value  # initial estimated value
        self.kalman_gain = 0  # initial Kalman gain

    def update(self, measurement):
        # update Kalman gain
        self.kalman_gain = self.estimated_error / (self.estimated_error + self.measurement_variance)
        
        # update estimate with measurement
        self.value = self.value + self.kalman_gain * (measurement - self.value)
        
        # update estimated error
        self.estimated_error = (1 - self.kalman_gain) * self.estimated_error + abs(self.value) * self.process_variance

        return self.value

# example list of noisy temperature measurements
temperature_measurements = [22.1, 22.5, 23.0, 22.8, 23.3, 23.5, 23.2, 23.7, 24.0, 23.9]

# Kalman filter parameters
process_variance = 1e-3  # small process noise
measurement_variance = 0.1  # assume some measurement noise
initial_estimated_error = 1.0  # initial error in estimation

# init Kalman filter
kf = KalmanFilter(process_variance, measurement_variance, initial_estimated_error, initial_value=temperature_measurements[0])

# apply Kalman filter to temperature measurements
filtered_temperatures = []

for measurement in temperature_measurements:
    filtered_temp = kf.update(measurement)
    filtered_temperatures.append(filtered_temp)
    print("Raw temperature:", measurement, "Filtered temperature:", filtered_temp)
```


### Explanation

1. `KalmanFilter` class: This class initializes with parameters for process noise,
    measurement noise, estimated error, and an initial value.
	- `process_variance`: Represents the uncertainty in the process (e.g. how much
      we expect the temperature might naturally vary).
	- `measurement_variance`: Represents the noise in the temperature measurements.
	- `estimated_error`: The initial guess for the error in the estimate.

2. `update` function: Each time a new temperature measurement is read, we call
    update, which:
	- Calculates the Kalman gain based on the current estimate and the measurement
      variance.
	- Updates the current estimate by blending the previous estimate and the new
      measurement based on the Kalman gain.
	- Adjusts the estimated error for the next iteration.

3. Example: The code then applies this filter to a list of temperature
   measurements and prints both the raw and filtered values for each reading.


### Example

For a list of temperature readings, you'd see an output like this:

```shell
Raw temperature: 22.1 Filtered temperature: 22.1
Raw temperature: 22.5 Filtered temperature: 22.3
Raw temperature: 23.0 Filtered temperature: 22.6
Raw temperature: 22.8 Filtered temperature: 22.7
...
```

This Kalman filter helps smooth out the noise, giving a more stable reading for
applications where precise temperature control is needed.


### Some observations

1. Smoothing: The filtered temperature changes more gradually compared to the raw temperature.
   - Raw temperature jumps from 22.5 to 23.0, a change of 0.5.
   - Filtered temperature only increases from 22.312 to 22.608, a smaller, smoother adjustment.

2. Lag effect: The filtered temperature lags slightly behind rapid changes in the raw temperature.
   This is a common feature of Kalman filters, which balance between the predicted state (from prior
   measurements) and the new measurement.
   - Raw temperature increases to 24.0, but the filtered temperature is still at 23.607.

3. Noise reduction: Sudden fluctuations in the raw temperature have a diminished effect on the
   filtered output.
   - Raw temperature briefly drops to 23.2, but the filtered output remains close to its trajectory
     at 23.163, reflecting less sensitivity to outliers or noise.

4. Adaptive estimation: The filter dynamically adjusts its trust in the raw measurement versus its
   internal model. This allows it to handle fluctuations without overreacting, while still adapting
   over time to reflect underlying trends.

