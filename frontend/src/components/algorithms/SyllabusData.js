// Generate data points for chart with fewer points to reduce clutter
const generateData = (maxN, fFunc, gFunc, hFunc) => {
  const data = [];
  const step = Math.max(1, Math.floor(maxN / 15)); // fewer data points for cleaner look
  for (let n = 1; n <= maxN; n += step) {
    data.push({
      n,
      fn: Number(fFunc(n).toFixed(2)),
      gn: Number(gFunc(n).toFixed(2)),
      ...(hFunc ? { hn: Number(hFunc(n).toFixed(2)) } : {})
    });
  }
  return data;
};

export const ALGORITHM_SYLLABUS_DATA = {
  'boyer-moore': {
    title: 'Boyer-Moore String Matching (Horspool)',
    pseudocode: `ALGORITHM HorspoolMatching(P[0..m-1], T[0..n-1])
// Implements Horspool's algorithm for string matching
// Input: Pattern P[0..m-1] and text T[0..n-1]
// Output: The index of the left end of the first matching substring
ShiftTable(P[0..m-1])
i <- m - 1
while i <= n - 1 do
    k <- 0
    while k <= m - 1 and P[m - 1 - k] = T[i - k] do
        k <- k + 1
    if k = m
        return i - m + 1
    else
        i <- i + Shift[T[i]]
return -1`,
    derivation: [
      "Time Complexity Derivation:",
      "1. Preprocessing (Shift Table): The ShiftTable algorithm initializes an array of size |Σ| (alphabet size) to m (pattern length), which takes O(|Σ|) time. It then scans the pattern P of length m from left to right to update the table: Shift[P[j]] = m - 1 - j for 0 ≤ j ≤ m-2. This takes O(m) time. Therefore, preprocessing time is Θ(m + |Σ|).",
      "2. Worst-Case Analysis: The worst-case scenario occurs when the shift is exactly 1 at every step, and almost all characters match before a mismatch is found (e.g., T='AAAAA', P='BAAAA'). For a text of length n and pattern of length m, there are (n - m + 1) alignments. At each alignment, m comparisons are made. Thus, worst-case time complexity is O(m * (n - m + 1)) ≈ O(nm).",
      "3. Average/Best-Case Analysis: In typical English text, characters mismatch almost immediately, and the bad character often doesn't exist in the pattern. This allows the algorithm to shift by the entire pattern length m. The number of alignments checked is roughly n/m. Therefore, the average and best-case time complexity is O(n/m), making it sub-linear and extremely fast in practice.",
      "",
      "Space Complexity Derivation:",
      "The algorithm constructs a shift table to map every possible character in the alphabet to a shift value. The size of this table is purely dependent on the alphabet size |Σ| (e.g., 256 for ASCII). Therefore, the space complexity is strictly O(|Σ|), which is constant space independent of n or m."
    ],
    chartData: generateData(100, n => n * 5, n => n * 10, n => n / 5)
  },
  'huffman': {
    title: 'Huffman Coding',
    pseudocode: `ALGORITHM Huffman(C)
// Implements Huffman's algorithm for constructing a Huffman tree
// Input: A collection C of n characters and their frequencies
// Output: A Huffman tree for C
n <- |C|
Q <- C  // Initialize priority queue Q with C (Min-Heap)
for i <- 1 to n - 1 do
    allocate a new node z
    z.left <- x <- Extract-Min(Q)
    z.right <- y <- Extract-Min(Q)
    z.freq <- x.freq + y.freq
    Insert(Q, z)
return Extract-Min(Q) // Return the root of the tree`,
    derivation: [
      "Time Complexity Derivation:",
      "1. Heap Initialization: Building the initial min-heap from n characters using the bottom-up Build-Heap algorithm takes strictly O(n) time.",
      "2. Tree Construction Loop: The loop executes exactly n - 1 times, as each iteration reduces the number of trees in the forest by 1.",
      "3. Operations within Loop: Each iteration performs two Extract-Min operations and one Insert operation on a min-heap containing at most n elements. Each heap operation (Extract-Min or Insert) takes O(log n) time.",
      "4. Total Time Calculation: The total time for the loop is (n - 1) * O(log n) = O(n log n). Adding the initialization time O(n), the overall time complexity is exactly O(n log n).",
      "Note: If the input frequencies are pre-sorted, Huffman coding can be optimized to O(n) using two standard queues.",
      "",
      "Space Complexity Derivation:",
      "1. The min-heap Q stores at most n leaf nodes and generates n - 1 internal nodes, totaling 2n - 1 nodes.",
      "2. Thus, the auxiliary space required to store the Huffman Tree and the Priority Queue is O(n), where n is the number of unique characters."
    ],
    chartData: generateData(50, n => n * Math.log2(n), n => 2 * n * Math.log2(n))
  },
  'merge-sort': {
    title: 'Merge Sort',
    pseudocode: `ALGORITHM MergeSort(A[0..n-1])
// Sorts array A[0..n-1] by recursive merge sort
// Input: An array A[0..n-1] of orderable elements
// Output: Array A[0..n-1] sorted in nondecreasing order
if n > 1
    copy A[0..floor(n/2)-1] to B[0..floor(n/2)-1]
    copy A[floor(n/2)..n-1] to C[0..ceil(n/2)-1]
    MergeSort(B)
    MergeSort(C)
    Merge(B, C, A)

ALGORITHM Merge(B[0..p-1], C[0..q-1], A[0..p+q-1])
// Merges two sorted arrays into one sorted array
i <- 0; j <- 0; k <- 0
while i < p and j < q do
    if B[i] <= C[j]
        A[k] <- B[i]; i <- i + 1
    else
        A[k] <- C[j]; j <- j + 1
    k <- k + 1
if i = p
    copy C[j..q-1] to A[k..p+q-1]
else
    copy B[i..p-1] to A[k..p+q-1]`,
    derivation: [
      "Time Complexity Derivation:",
      "1. Divide Step: Computing the middle of the array takes constant time O(1).",
      "2. Conquer Step: We recursively sort two subarrays, each of size n/2. This contributes 2T(n/2) to the running time.",
      "3. Combine Step (Merge): The Merge procedure takes two sorted arrays of size n/2 and merges them into an array of size n. In the worst case, it makes n - 1 comparisons, taking Θ(n) time.",
      "4. Recurrence Relation: The overall time T(n) is described by: T(n) = 2T(n/2) + Θ(n) for n > 1, with T(1) = Θ(1).",
      "5. Solving the Recurrence (Master Theorem): Here, a = 2, b = 2, and f(n) = n^1. Since log_b(a) = log_2(2) = 1, we are in Case 2 of the Master Theorem (f(n) = Θ(n^log_b(a))). Therefore, T(n) = Θ(n log n).",
      "This bound is tight for all cases (Best, Average, Worst) because the array is always split exactly in half regardless of the input's sorted state.",
      "",
      "Space Complexity Derivation:",
      "1. Auxiliary Arrays: The Merge operation requires allocating temporary arrays B and C, which together take up to n elements. Thus, O(n) auxiliary memory is needed.",
      "2. Call Stack: The recursion tree has a depth of log n, requiring O(log n) stack space. Since O(n) dominates O(log n), the total space complexity is strictly O(n)."
    ],
    chartData: generateData(50, n => n * Math.log2(n), n => 1.5 * n * Math.log2(n), n => 0.5 * n * Math.log2(n))
  },
  'priority-queue': {
    title: 'Priority Queue (Heap Operations)',
    pseudocode: `ALGORITHM HeapifyUp(A, i)
// Restores heap property after insertion at index i
while i > 0 and A[Parent(i)] < A[i] do
    Swap(A[Parent(i)], A[i])
    i <- Parent(i)

ALGORITHM HeapifyDown(A, i, n)
// Restores heap property for a node at index i down to size n
while LeftChild(i) <= n do
    maxChild <- LeftChild(i)
    if RightChild(i) <= n and A[RightChild(i)] > A[maxChild]
        maxChild <- RightChild(i)
    if A[i] < A[maxChild]
        Swap(A[i], A[maxChild])
        i <- maxChild
    else break`,
    derivation: [
      "Time Complexity Derivation:",
      "1. Height of a Heap: A binary heap of n elements is a nearly complete binary tree, which mathematically guarantees its height h is bounded by O(log n).",
      "2. Insert Operation: A new element is added at the end of the array (leaf node). To restore the heap property, HeapifyUp swaps it with its parent up to the root. In the worst case, it travels the full height of the tree. Thus, Insertion takes O(log n) time.",
      "3. Extract-Max Operation: The root (maximum element) is removed and replaced with the last leaf element. HeapifyDown then pushes this element down the tree by swapping with the larger child. This also traverses at most the height of the tree, taking O(log n) time.",
      "4. Build-Heap (Floyd's Method): If building a heap from an unsorted array, we call HeapifyDown from the middle of the array down to index 0. While a naive approach takes O(n log n), rigorous mathematical summation shows that most nodes are at the bottom and travel short distances. The sum Σ (h/2^h) converges to a constant. Thus, Build-Heap runs in strict O(n) time.",
      "",
      "Space Complexity Derivation:",
      "A binary heap is perfectly mapped to an array without needing explicit pointers for children/parents. Parent(i) = floor((i-1)/2), LeftChild(i) = 2i+1. Thus, it only requires the O(n) space for the array itself, making it an in-place data structure."
    ],
    chartData: generateData(50, n => Math.log2(n), n => 2 * Math.log2(n))
  },
  'floyd-warshall': {
    title: 'Floyd-Warshall (All-Pairs Shortest Path)',
    pseudocode: `ALGORITHM FloydWarshall(W[1..n, 1..n])
// Implements Floyd's algorithm for all-pairs shortest paths
// Input: The weight matrix W of a graph with no negative-weight cycles
// Output: The distance matrix D of shortest paths' lengths
D <- W
for k <- 1 to n do
    for i <- 1 to n do
        for j <- 1 to n do
            D[i,j] <- min(D[i,j], D[i,k] + D[k,j])
return D`,
    derivation: [
      "Time Complexity Derivation:",
      "1. Loop Structure: The algorithm consists of exactly three nested loops. The outer loop variable 'k' iterates from 1 to n (representing intermediate vertices). The middle loop 'i' iterates from 1 to n (source vertices), and the inner loop 'j' iterates from 1 to n (destination vertices).",
      "2. Inner Loop Execution: The core operation inside the innermost loop evaluates `min(D[i,j], D[i,k] + D[k,j])`. This consists of array lookups, one addition, and one comparison, which collectively execute in constant O(1) time.",
      "3. Total Executions: Since the limits of all three loops are entirely independent and exactly n, the total number of times the inner statement executes is exactly n * n * n = n^3.",
      "4. Final Time Complexity: Because there are no early exits or variable loop bounds, the time complexity is strictly bounded both above and below. Therefore, T(n) = Θ(n³).",
      "",
      "Space Complexity Derivation:",
      "The algorithm maintains an n × n distance matrix D to store the shortest path distances between every pair of vertices. Therefore, the total memory required is strictly proportional to n^2. The space complexity is Θ(n²)."
    ],
    chartData: generateData(50, n => n * n * n, n => 1.5 * n * n * n, n => 0.5 * n * n * n)
  }
};
