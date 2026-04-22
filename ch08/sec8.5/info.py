import math
import heapq
from collections import Counter


def entropy(text: str) -> float:
    n = len(text)
    counts = Counter(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


class HuffNode:
    __slots__ = ('sym', 'freq', 'left', 'right')

    def __init__(self, sym, freq, left=None, right=None):
        self.sym   = sym
        self.freq  = freq
        self.left  = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


def build_tree(text: str) -> HuffNode | None:
    counts = Counter(text)
    heap = [HuffNode(sym, freq) for sym, freq in counts.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        heapq.heappush(heap, HuffNode(None, a.freq + b.freq, a, b))
    return heap[0] if heap else None


def _collect_codes(node: HuffNode, prefix: str, table: dict) -> None:
    if node.sym is not None:
        table[node.sym] = prefix or '0'
    else:
        _collect_codes(node.left,  prefix + '0', table)
        _collect_codes(node.right, prefix + '1', table)


def encode(text: str) -> tuple[str, HuffNode, dict]:
    if not text:
        return '', None, {}
    root  = build_tree(text)
    table = {}
    _collect_codes(root, '', table)
    bitstring = ''.join(table[c] for c in text)
    return bitstring, root, table


def decode(bits: str, root: HuffNode) -> str:
    if root.sym is not None:
        return root.sym * len(bits)
    result, node = [], root
    for bit in bits:
        node = node.left if bit == '0' else node.right
        if node.sym is not None:
            result.append(node.sym)
            node = root
    return ''.join(result)


def report(text: str) -> None:
    h          = entropy(text)
    bits, root, table = encode(text)
    n          = len(text)
    orig_bits  = n * 8
    comp_bits  = len(bits)
    avg_len    = comp_bits / n

    label = repr(text) if len(text) <= 20 else repr(text[:20] + '...')
    print(f"Text:          {label}")
    print(f"  Entropy:     {h:.4f} bits/symbol  (theoretical minimum)")
    print(f"  Avg code:    {avg_len:.4f} bits/symbol  (Huffman actual)")
    print(f"  Gap:         {avg_len - h:.4f} bits/symbol  (redundancy)")
    print(f"  Original:    {orig_bits} bits (8-bit ASCII)")
    print(f"  Compressed:  {comp_bits} bits")
    print(f"  Ratio:       {100.0 * comp_bits / orig_bits:.1f}%")
    # Print codes sorted by length then symbol
    sorted_codes = sorted(table.items(), key=lambda kv: (len(kv[1]), kv[0]))
    codes_str = '  '.join(
        f"{'SPC' if s == ' ' else repr(s)}={c}" for s, c in sorted_codes
    )
    print(f"  Codes:       {codes_str}")
    # Verify round-trip
    assert decode(bits, root) == text, "decode mismatch!"
    print()


if __name__ == '__main__':
    examples = [
        "aaabbc",
        "hello",
        "hello world",
        "aaaaaa",
        "abcdefgh",
        "the quick brown fox jumps over the lazy dog",
    ]
    for t in examples:
        report(t)
