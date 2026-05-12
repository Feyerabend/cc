import random

# Define a Unit class to represent individual neurons in the network.
class Unit:
    def __init__(self, unit_id, initial_activation=0.0, is_input=False, is_output=False, is_hidden=False):
        """
        Initializes a unit (neuron) in the neural network.

        Args:
            unit_id (str): A unique identifier for the unit.
            initial_activation (float): The starting activation level for the unit.
            is_input (bool): True if this unit is an input unit.
            is_output (bool): True if this unit is an output unit.
            is_hidden (bool): True if this unit is a hidden unit.
        """
        self.id = unit_id
        self.activation = initial_activation
        # As per the text, a unit's output is typically its activation.
        self.output = initial_activation 
        self.is_input = is_input
        self.is_output = is_output
        self.is_hidden = is_hidden

class NeuralNetwork:
    def __init__(self):
        """
        Initializes the neural network structure.
        Stores units, weights, and categorizes units by type.
        """
        self.units = {}  # Dictionary to store Unit objects by their ID
        # Weights are stored as a dictionary: {(from_unit_id, to_unit_id): weight_value}
        self.weights = {} 
        self.input_unit_ids = []
        self.hidden_unit_ids = []
        self.output_unit_ids = []

    def add_unit(self, unit_id, is_input=False, is_output=False, is_hidden=False):
        """
        Adds a new unit to the network.

        Args:
            unit_id (str): Unique identifier for the unit.
            is_input (bool): Whether this unit is an input unit.
            is_output (bool): Whether this unit is an output unit.
            is_hidden (bool): Whether this unit is a hidden unit.
        """
        if unit_id in self.units:
            print(f"Warning: Unit '{unit_id}' already exists. Skipping addition.")
            return

        unit = Unit(unit_id, is_input=is_input, is_output=is_output, is_hidden=is_hidden)
        self.units[unit_id] = unit
        if is_input:
            self.input_unit_ids.append(unit_id)
        elif is_output:
            self.output_unit_ids.append(unit_id)
        elif is_hidden:
            self.hidden_unit_ids.append(unit_id)

    def add_connection(self, from_unit_id, to_unit_id, initial_weight=None):
        """
        Adds a weighted connection (link) between two units.

        Args:
            from_unit_id (str): The ID of the source unit.
            to_unit_id (str): The ID of the destination unit.
            initial_weight (float, optional): The starting weight for the connection.
                                               If None, a random weight between -1 and 1 is used.
        """
        if from_unit_id not in self.units or to_unit_id not in self.units:
            print(f"Error: Cannot add connection. Unit IDs '{from_unit_id}' or '{to_unit_id}' do not exist.")
            return

        if (from_unit_id, to_unit_id) in self.weights:
            print(f"Warning: Connection from '{from_unit_id}' to '{to_unit_id}' already exists. Skipping addition.")
            return

        # Initialize weight randomly if not provided
        if initial_weight is None:
            initial_weight = random.uniform(-1, 1) 
        self.weights[(from_unit_id, to_unit_id)] = initial_weight

    def set_input(self, input_values):
        """
        Sets the activation levels for the input units.

        Args:
            input_values (list): A list of values corresponding to the input units
                                 in the order they were added.
        """
        if len(input_values) != len(self.input_unit_ids):
            print(f"Error: Input values count ({len(input_values)}) does not match "
                  f"number of input units ({len(self.input_unit_ids)}).")
            return

        for i, unit_id in enumerate(self.input_unit_ids):
            self.units[unit_id].activation = input_values[i]
            self.units[unit_id].output = input_values[i] # Update output as well

    def _get_incoming_connections(self, to_unit_id):
        """
        Helper method to retrieve all connections leading into a specific unit.

        Args:
            to_unit_id (str): The ID of the destination unit.

        Returns:
            list: A list of tuples (from_unit_id, weight) for incoming connections.
        """
        incoming = []
        for (from_id, to_id), weight in self.weights.items():
            if to_id == to_unit_id:
                incoming.append((from_id, weight))
        return incoming

    def _calculate_total_input(self, unit_id):
        """
        Calculates the sum of weighted inputs for a given unit, as per the text:
        input_yx = w_yx * output_y, and total input is sum of such products.

        Args:
            unit_id (str): The ID of the unit for which to calculate total input.

        Returns:
            float: The sum of weighted inputs.
        """
        total_input = 0.0
        incoming_connections = self._get_incoming_connections(unit_id)
        for from_id, weight in incoming_connections:
            # from_id is 'y' and unit_id is 'x' in the w_yx * output_y formula.
            # 'weight' here is w_yx, and self.units[from_id].output is output_y.
            total_input += weight * self.units[from_id].output
        return total_input

    def activate(self, activation_type="linear", threshold=0.5):
        """
        Activates all non-input units in the network based on their inputs.
        Assumes a feedforward processing order (hidden units before output units).

        Args:
            activation_type (str): The type of activation function to use ('linear' or 'binary').
            threshold (float): The threshold for the 'binary' activation function.
        """
        # Define processing order: first hidden, then output units.
        # This assumes a simple feedforward architecture.
        processing_order_ids = []
        processing_order_ids.extend(self.hidden_unit_ids)
        processing_order_ids.extend(self.output_unit_ids)
        
        # Update activations for non-input units based on their calculated total input
        for unit_id in processing_order_ids:
            if not self.units[unit_id].is_input: # Input units are set directly via set_input
                total_input = self._calculate_total_input(unit_id)
                
                if activation_type == "linear":
                    # For linear activation, the new activation is simply the total input.
                    self.units[unit_id].activation = total_input
                elif activation_type == "binary":
                    # For binary activation, the new activation is 1 if input > threshold, else 0.
                    self.units[unit_id].activation = 1.0 if total_input > threshold else 0.0
                else:
                    print(f"Error: Unsupported activation type '{activation_type}'. Use 'linear' or 'binary'.")
                    return # Exit to avoid further errors

                # Update the unit's output to reflect its new activation
                self.units[unit_id].output = self.units[unit_id].activation

    def get_output_pattern(self):
        """
        Retrieves the activation levels of all output units.

        Returns:
            dict: A dictionary where keys are output unit IDs and values are their activations.
        """
        return {uid: self.units[uid].activation for uid in self.output_unit_ids}

    def train_hebbian(self, learning_rate):
        """
        Applies the Hebbian learning rule to all connections in the network.
        The rule states: delta_w_xy = learning_rate * activation_x * activation_y,
        where x is the 'from' unit and y is the 'to' unit. Weights are updated
        if both connected units are active or similarly activated.

        Args:
            learning_rate (float): The learning rate (l) for weight adjustment.
        """
        new_weights = self.weights.copy() # Create a copy to update safely
        for (from_id, to_id), current_weight in self.weights.items():
            # In the formula w_xy(t+1) = w_xy(t) + l * a_x(t) * a_y(t)
            # from_id is 'x' (source) and to_id is 'y' (destination).
            # The current activations (outputs) are used.
            delta_w = learning_rate * self.units[from_id].output * self.units[to_id].output
            new_weights[(from_id, to_id)] = current_weight + delta_w
        self.weights = new_weights # Apply all changes at once

    def train_delta(self, target_outputs, learning_rate):
        """
        Applies the Delta learning rule to weights leading into output units.
        The rule states: delta_w_yx = learning_rate * (d_x - a_x) * a_y,
        where d_x is the desired output for unit x (an output unit), 
        a_x is the actual output of unit x, and a_y is the output of unit y 
        (an input to unit x).

        Args:
            target_outputs (dict): A dictionary mapping output unit IDs to their desired activation values.
            learning_rate (float): The learning rate (l) for weight adjustment.
        """
        new_weights = self.weights.copy() # Create a copy to update safely
        
        # Iterate over each output unit to calculate its error and update incoming weights
        for output_unit_id in self.output_unit_ids:
            if output_unit_id not in target_outputs:
                print(f"Warning: No target output provided for unit '{output_unit_id}'. Skipping Delta rule for this unit.")
                continue

            actual_output_x = self.units[output_unit_id].activation
            desired_output_x = target_outputs[output_unit_id]
            
            error_x = desired_output_x - actual_output_x # (d_x - a_x)
            
            # Find all connections (y -> x) leading into this output unit 'x'
            incoming_connections = self._get_incoming_connections(output_unit_id)
            for from_id_y, _ in incoming_connections: # from_id_y is 'y' in the formula
                output_y = self.units[from_id_y].output # a_y
                
                # Calculate the weight change for this specific connection
                delta_w = learning_rate * error_x * output_y
                
                # Update the weight for the connection (from_id_y, output_unit_id)
                new_weights[(from_id_y, output_unit_id)] += delta_w
                
        self.weights = new_weights # Apply all changes at once

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Demonstrating a simple AND gate with Binary Activation and Delta Rule ---")

    nn = NeuralNetwork()

    # Add input units
    nn.add_unit("A", is_input=True)
    nn.add_unit("B", is_input=True)
    # Add an output unit
    nn.add_unit("C", is_output=True)

    # Add connections from input to output unit
    # Initial weights can be random or chosen for demonstration
    nn.add_connection("A", "C", initial_weight=0.1) 
    nn.add_connection("B", "C", initial_weight=0.1)

    # Define training data for AND gate
    # (input_values, target_output_for_C)
    training_data = [
        ([0, 0], {"C": 0}),
        ([0, 1], {"C": 0}),
        ([1, 0], {"C": 0}),
        ([1, 1], {"C": 1})
    ]

    learning_rate = 0.1
    threshold = 0.5 # For binary activation
    epochs = 100 # Number of training iterations

    print(f"\nInitial Weights: {nn.weights}")

    for epoch in range(epochs):
        total_error = 0
        for inputs, targets in training_data:
            # 1. Set input values
            nn.set_input(inputs)
            
            # 2. Activate the network (forward pass)
            nn.activate(activation_type="binary", threshold=threshold)
            
            # 3. Get current output
            output = nn.get_output_pattern()["C"] # Get output for unit 'C'
            
            # Calculate error for this training example
            error = targets["C"] - output
            total_error += abs(error)

            # 4. Train with Delta rule
            nn.train_delta(targets, learning_rate)
        
        # Print progress every few epochs
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"\nEpoch {epoch+1}, Total Absolute Error: {total_error:.4f}")
            print(f"Current Weights: {nn.weights}")
            # Test after training iteration to see performance
            print("Testing current network:")
            for inputs, _ in training_data:
                nn.set_input(inputs)
                nn.activate(activation_type="binary", threshold=threshold)
                current_output = nn.get_output_pattern()["C"]
                print(f"  Input: {inputs} -> Predicted Output: {current_output}")

    print("\n--- Training Complete ---")
    print(f"Final Weights: {nn.weights}")

    print("\n--- Final Test of AND Gate ---")
    for inputs, targets in training_data:
        nn.set_input(inputs)
        nn.activate(activation_type="binary", threshold=threshold)
        output = nn.get_output_pattern()["C"]
        print(f"Input: {inputs}, Target: {targets['C']}, Predicted: {output}")

    print("\n--- Demonstrating Hebbian Learning (Conceptual) ---")
    # Reset network for Hebbian example
    hebb_nn = NeuralNetwork()
    hebb_nn.add_unit("X", is_input=True)
    hebb_nn.add_unit("Y", is_output=True) # Could be any unit type, but simplifies example
    hebb_nn.add_connection("X", "Y", initial_weight=0.0) # Start with zero weight

    print(f"Initial Hebbian Weight (X,Y): {hebb_nn.weights[('X', 'Y')]}")
    hebb_learning_rate = 0.5

    # Scenario 1: X and Y are both active (Hebbian: strengthen connection)
    print("\nScenario 1: X=1, Y=1 (simultaneous activation)")
    hebb_nn.set_input([1]) # Set X to 1
    # Manually set Y's activation for this conceptual example, assuming it became 1
    hebb_nn.units["Y"].activation = 1.0 
    hebb_nn.units["Y"].output = 1.0 
    hebb_nn.train_hebbian(hebb_learning_rate)
    print(f"Weight after X=1, Y=1: {hebb_nn.weights[('X', 'Y')]}")

    # Scenario 2: X active, Y inactive (Hebbian: no change if product is 0, or weaken if signs differ)
    # Based on the text, if one is 1 and other 0, product is 0, so no change.
    print("\nScenario 2: X=1, Y=0 (X active, Y inactive)")
    hebb_nn.set_input([1]) 
    hebb_nn.units["Y"].activation = 0.0
    hebb_nn.units["Y"].output = 0.0
    hebb_nn.train_hebbian(hebb_learning_rate)
    print(f"Weight after X=1, Y=0: {hebb_nn.weights[('X', 'Y')]}")

    # Scenario 3: X and Y are both inactive (Hebbian: strengthen if product of negative activations is positive)
    # The text says "same sign (positive or negative)", so for -1, -1 it should strengthen
    # If using 0,0 for inactive, product is 0, so no change.
    # Let's show with activations that result in non-zero product but same sign
    print("\nScenario 3: X=-1, Y=-1 (both negatively active/same sign)")
    hebb_nn_neg = NeuralNetwork()
    hebb_nn_neg.add_unit("X_neg", is_input=True)
    hebb_nn_neg.add_unit("Y_neg", is_output=True)
    hebb_nn_neg.add_connection("X_neg", "Y_neg", initial_weight=0.0)
    print(f"Initial Hebbian Weight (X_neg,Y_neg): {hebb_nn_neg.weights[('X_neg', 'Y_neg')]}")

    hebb_nn_neg.set_input([-1]) 
    hebb_nn_neg.units["Y_neg"].activation = -1.0
    hebb_nn_neg.units["Y_neg"].output = -1.0
    hebb_nn_neg.train_hebbian(hebb_learning_rate)
    print(f"Weight after X=-1, Y=-1: {hebb_nn_neg.weights[('X_neg', 'Y_neg')]}")

# A script that illustrates a network from LINDSTROM.md
# as early development in neural networks.
