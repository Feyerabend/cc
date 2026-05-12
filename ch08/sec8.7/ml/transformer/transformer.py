import math
import random
from typing import List

class Transformer:
    def __init__(self, seq_len: int, d_model: int, num_heads: int):
        if d_model % num_heads != 0:
            raise ValueError(f"d_model ({d_model}) must be divisible by num_heads ({num_heads})")
        self.seq_len = seq_len
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        # Initialize weights using Gaussian distribution scaled by sqrt(d_model)
        self.W_q = self._initialize_weights(d_model, d_model)
        self.W_k = self._initialize_weights(d_model, d_model)
        self.W_v = self._initialize_weights(d_model, d_model)
        self.W_o = self._initialize_weights(d_model, d_model)

        # Feedforward network
        self.W_ff1 = self._initialize_weights(d_model, d_model)
        self.W_ff2 = self._initialize_weights(d_model, d_model)

    def _initialize_weights(self, rows: int, cols: int) -> List[List[float]]:
        """Initialize weights with random values scaled by sqrt(d_model)."""
        return [
            [random.gauss(0, 1) / math.sqrt(self.d_model) for _ in range(cols)]
            for _ in range(rows)
        ]

    def positional_encoding(self, seq_len: int, d_model: int) -> List[List[float]]:
        """Generate positional encoding for the input sequence."""
        pos_enc = [[0.0 for _ in range(d_model)] for _ in range(seq_len)]
        for pos in range(seq_len):
            for i in range(0, d_model, 2):
                pos_enc[pos][i] = math.sin(pos / (10000 ** (i / d_model)))
                if i + 1 < d_model:
                    pos_enc[pos][i + 1] = math.cos(pos / (10000 ** (i / d_model)))
        return pos_enc

    def matmul(self, A: List, B: List) -> List:
        """Matrix multiplication for 3D (batch of 2D) and 2D matrices."""
        # Get dimensions of A
        batch_size_A = len(A)
        rows_A = len(A[0])
        cols_A = len(A[0][0])

        # Determine if B is 2D or 3D
        if not isinstance(B[0], list):
            raise ValueError(f"B must be a 2D or 3D list, but B[0] is not a list")
        is_B_2d = isinstance(B[0][0], (int, float))  # 2D if B[0][0] is a number
        if is_B_2d:
            rows_B = len(B)
            cols_B = len(B[0])
            batch_size_B = 1  # Treat 2D B as a single "batch"
        else:
            batch_size_B = len(B)
            rows_B = len(B[0])
            cols_B = len(B[0][0])

        # Check compatibility
        if cols_A != rows_B:
            raise ValueError(f"Incompatible dimensions for matrix multiplication: A ({batch_size_A}, {rows_A}, {cols_A}) and B ({rows_B}, {cols_B})")
        if not is_B_2d and batch_size_A != batch_size_B:
            raise ValueError(f"Batch sizes incompatible: A ({batch_size_A}, {rows_A}, {cols_A}) and B ({batch_size_B}, {rows_B}, {cols_B})")

        # Case 1: B is 2D - apply B to each batch element of A
        if is_B_2d:
            result = [
                [
                    [
                        sum(A[b][i][k] * B[k][j] for k in range(cols_A))
                        for j in range(cols_B)
                    ]
                    for i in range(rows_A)
                ]
                for b in range(batch_size_A)
            ]
        # Case 2: Both A and B are 3D - batch matrix multiplication
        else:
            result = [
                [
                    [
                        sum(A[b][i][k] * B[b][k][j] for k in range(cols_A))
                        for j in range(cols_B)
                    ]
                    for i in range(rows_A)
                ]
                for b in range(batch_size_A)
            ]
        return result

    def softmax(self, scores: List[List[List[float]]]) -> List[List[List[float]]]:
        """Compute softmax over the last dimension of a 3D list."""
        result = []
        for batch in scores:
            batch_result = []
            for row in batch:
                max_val = max(row)
                exp_scores = [math.exp(s - max_val) for s in row]
                sum_exp = sum(exp_scores)
                batch_result.append([s / sum_exp for s in exp_scores])
            result.append(batch_result)
        return result

    def transpose(self, matrix: List[List[List[float]]]) -> List[List[List[float]]]:
        """Transpose the last two dimensions of a 3D matrix."""
        batch_size = len(matrix)
        rows = len(matrix[0])
        cols = len(matrix[0][0])
        return [
            [
                [matrix[b][j][i] for j in range(rows)]
                for i in range(cols)
            ]
            for b in range(batch_size)
        ]

    def scaled_dot_product_attention(self, Q: List, K: List, V: List) -> List:
        """Scaled dot-product attention."""
        K_T = self.transpose(K)
        scores = self.matmul(Q, K_T)
        scores = [
            [
                [s / math.sqrt(self.head_dim) for s in row]
                for row in batch
            ]
            for batch in scores
        ]
        attention_weights = self.softmax(scores)
        return self.matmul(attention_weights, V)

    def multi_head_attention(self, x: List[List[List[float]]]) -> List[List[List[float]]]:
        """Multi-head attention mechanism."""
        batch_size, seq_len, d_model = len(x), len(x[0]), len(x[0][0])

        Q = self.matmul(x, self.W_q)
        K = self.matmul(x, self.W_k)
        V = self.matmul(x, self.W_v)

        Q_heads = self._reshape_heads(Q, batch_size, seq_len)
        K_heads = self._reshape_heads(K, batch_size, seq_len)
        V_heads = self._reshape_heads(V, batch_size, seq_len)

        heads = [
            self.scaled_dot_product_attention(Q_heads[i], K_heads[i], V_heads[i])
            for i in range(self.num_heads)
        ]

        concatenated = self._concat_heads(heads, batch_size, seq_len)
        return self.matmul(concatenated, self.W_o)

    def _reshape_heads(self, x: List, batch_size: int, seq_len: int) -> List:
        """Reshape and split into multiple heads, returning a list of heads across all batches."""
        heads = []
        for h in range(self.num_heads):
            head = [
                [
                    x[b][s][h * self.head_dim : (h + 1) * self.head_dim]
                    for s in range(seq_len)
                ]
                for b in range(batch_size)
            ]
            heads.append(head)
        return heads

    def _concat_heads(self, heads: List, batch_size: int, seq_len: int) -> List:
        """Concatenate attention heads."""
        return [
            [
                [
                    item for h in range(self.num_heads) for item in heads[h][b][s]
                ]
                for s in range(seq_len)
            ]
            for b in range(batch_size)
        ]

    def feedforward(self, x: List[List[List[float]]]) -> List[List[List[float]]]:
        """Feedforward network with ReLU activation."""
        batch_size = len(x)
        seq_len = len(x[0])
        ff1_out = [
            [
                [
                    max(0.0, sum(x[b][s][k] * self.W_ff1[k][j] for k in range(self.d_model)))
                    for j in range(self.d_model)
                ]
                for s in range(seq_len)
            ]
            for b in range(batch_size)
        ]
        ff2_out = self.matmul(ff1_out, self.W_ff2)
        return ff2_out

    def residual_addition(self, x: List, out: List) -> List:
        """Apply residual connection."""
        batch_size = len(x)
        return [
            [
                [x[b][s][i] + out[b][s][i] for i in range(self.d_model)]
                for s in range(self.seq_len)
            ]
            for b in range(batch_size)
        ]

    def forward(self, x: List[List[List[float]]]) -> List[List[List[float]]]:
        """Forward pass through the transformer."""
        batch_size, seq_len, d_model = len(x), len(x[0]), len(x[0][0])
        if seq_len != self.seq_len or d_model != self.d_model:
            raise ValueError(f"Input shape ({batch_size}, {seq_len}, {d_model}) incompatible with expected ({self.seq_len}, {self.d_model})")

        # Generate positional encoding and add to the input
        pos_enc = self.positional_encoding(seq_len, d_model)
        pos_enc_expanded = [pos_enc for _ in range(batch_size)]
        x = self.residual_addition(x, pos_enc_expanded)

        # Multi-head attention with residual connection
        attention_out = self.multi_head_attention(x)
        x = self.residual_addition(x, attention_out)

        # Feedforward network with residual connection
        ff_out = self.feedforward(x)
        x = self.residual_addition(x, ff_out)

        return x

# Example usage
def example_usage():
    seq_len = 4    # Sequence length (e.g., 4 tokens)
    d_model = 8    # Embedding size
    num_heads = 2  # Number of attention heads
    batch_size = 2 # Number of sequences in batch

    # Create a batch of dummy input data: batch_size=2, seq_len=4, d_model=8
    input_data = [
        [[random.gauss(0, 1) for _ in range(d_model)] for _ in range(seq_len)]
        for _ in range(batch_size)
    ]
    print(f"Input shape: ({batch_size}, {seq_len}, {d_model})")
    print("Sample input for first sequence:", input_data[0])

    # Create and run the transformer
    transformer = Transformer(seq_len, d_model, num_heads)
    output = transformer.forward(input_data)

    print(f"Output shape: ({len(output)}, {len(output[0])}, {len(output[0][0])})")
    print("Sample output for first sequence:", output[0])

if __name__ == "__main__":
    example_usage()

