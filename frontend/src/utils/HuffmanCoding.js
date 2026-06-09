/**
 * Huffman Coding Algorithm implementation
 * Used for lossless data compression
 */

class MinHeapNode {
  constructor(char, freq) {
    this.char = char;
    this.freq = freq;
    this.left = null;
    this.right = null;
  }
}

// Helper: Custom Min-Heap tailored for Huffman Nodes
class HuffmanMinHeap {
  constructor() {
    this.heap = [];
  }
  
  push(node) {
    this.heap.push(node);
    this.heapifyUp(this.heap.length - 1);
  }
  
  pop() {
    if (this.heap.length === 0) return null;
    if (this.heap.length === 1) return this.heap.pop();
    const top = this.heap[0];
    this.heap[0] = this.heap.pop();
    this.heapifyDown(0);
    return top;
  }
  
  heapifyUp(index) {
    let cur = index;
    while (cur > 0) {
      const parent = Math.floor((cur - 1) / 2);
      if (this.heap[cur].freq < this.heap[parent].freq) {
        [this.heap[cur], this.heap[parent]] = [this.heap[parent], this.heap[cur]];
        cur = parent;
      } else {
        break;
      }
    }
  }
  
  heapifyDown(index) {
    let cur = index;
    const len = this.heap.length;
    while (2 * cur + 1 < len) {
      let minChild = 2 * cur + 1;
      let rightChild = 2 * cur + 2;
      
      if (rightChild < len && this.heap[rightChild].freq < this.heap[minChild].freq) {
        minChild = rightChild;
      }
      
      if (this.heap[cur].freq > this.heap[minChild].freq) {
        [this.heap[cur], this.heap[minChild]] = [this.heap[minChild], this.heap[cur]];
        cur = minChild;
      } else {
        break;
      }
    }
  }
  
  size() {
    return this.heap.length;
  }
}

/**
 * Builds the Huffman Tree using the characters frequencies
 */
function buildHuffmanTree(text) {
  const freqMap = {};
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    freqMap[char] = (freqMap[char] || 0) + 1;
  }
  
  const minHeap = new HuffmanMinHeap();
  for (const char in freqMap) {
    minHeap.push(new MinHeapNode(char, freqMap[char]));
  }
  
  if (minHeap.size() === 1) {
    const node = new MinHeapNode(null, minHeap.heap[0].freq);
    node.left = minHeap.pop();
    return node;
  }
  
  while (minHeap.size() > 1) {
    const left = minHeap.pop();
    const right = minHeap.pop();
    
    const top = new MinHeapNode(null, left.freq + right.freq);
    top.left = left;
    top.right = right;
    
    minHeap.push(top);
  }
  
  return minHeap.pop();
}

/**
 * Generates the dictionary mapping characters to binary codes
 */
function generateCodes(node, prefix = "", codes = {}) {
  if (!node) return;
  
  // Is leaf node
  if (node.char !== null) {
    codes[node.char] = prefix || "0"; // Handle single char edge case
    return;
  }
  
  generateCodes(node.left, prefix + "0", codes);
  generateCodes(node.right, prefix + "1", codes);
  
  return codes;
}

/**
 * Compresses the given text into a binary string using Huffman Coding.
 * Returns the encoded string and the tree/codes needed to decode it.
 */
export function compressHuffman(text) {
  if (!text) return { encodedStr: "", codes: {}, tree: null };
  
  const tree = buildHuffmanTree(text);
  const codes = generateCodes(tree);
  
  let encodedStr = "";
  for (let i = 0; i < text.length; i++) {
    encodedStr += codes[text[i]];
  }
  
  // Calculating sizes
  const originalSizeBits = text.length * 8; // Assuming 8-bit ASCII characters
  const compressedSizeBits = encodedStr.length;
  
  return {
    encodedStr,
    codes,
    tree,
    originalSizeBits,
    compressedSizeBits,
    compressionRatio: ((1 - (compressedSizeBits / originalSizeBits)) * 100).toFixed(2)
  };
}

/**
 * Decompresses a Huffman encoded string back to original text using the Huffman Tree
 */
export function decompressHuffman(encodedStr, tree) {
  if (!encodedStr || !tree) return "";
  
  let decodedStr = "";
  let currentNode = tree;
  
  // Edge case for single character strings
  if (tree.left && !tree.right && tree.left.char !== null && !tree.char) {
      for(let i=0; i < encodedStr.length; i++){
          decodedStr += tree.left.char;
      }
      return decodedStr;
  }

  for (let i = 0; i < encodedStr.length; i++) {
    if (encodedStr[i] === '0') {
      currentNode = currentNode.left;
    } else {
      currentNode = currentNode.right;
    }
    
    if (currentNode.char !== null) { // Reached a leaf node
      decodedStr += currentNode.char;
      currentNode = tree; // Reset to root for next character
    }
  }
  
  return decodedStr;
}
