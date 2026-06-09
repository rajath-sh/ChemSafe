/**
 * Max-Heap Priority Queue for sorting Incidents
 */
export class PriorityQueue {
  constructor() {
    this.heap = [];
  }

  // Calculate the priority score of an incident
  // Higher score = Higher priority (bubbles up)
  static calculatePriority(incident) {
    let score = 0;
    
    // Base Severity Score
    const severityLower = (incident.severity || '').toLowerCase();
    if (severityLower === 'critical') score += 4000000000;
    else if (severityLower === 'high') score += 3000000000;
    else if (severityLower === 'medium') score += 2000000000;
    else if (severityLower === 'low') score += 1000000000;

    // Age Tie-Breaker
    // Subtract creation timestamp from a fixed future date so that OLDER incidents have a HIGHER tie-breaker score.
    // e.g. 2026 timestamp vs 2024 timestamp. 2024 is older, so it should get higher priority.
    // Time elapsed since 1970 in seconds
    try {
      const createdTime = new Date(incident.created_at || incident.timestamp || Date.now()).getTime();
      // We want older incidents to have a larger value.
      // So we can subtract the timestamp from a very large constant.
      const maxTime = new Date('2100-01-01').getTime(); 
      score += (maxTime - createdTime) / 1000; // adding seconds
    } catch (e) {
      // Fallback
    }
    
    return score;
  }

  // Get Parent/Child indices
  getParentIndex(i) { return Math.floor((i - 1) / 2); }
  getLeftChildIndex(i) { return 2 * i + 1; }
  getRightChildIndex(i) { return 2 * i + 2; }

  // Swap helper
  swap(i1, i2) {
    const temp = this.heap[i1];
    this.heap[i1] = this.heap[i2];
    this.heap[i2] = temp;
  }

  // Insert an incident into the Max-Heap
  insert(incident) {
    const score = PriorityQueue.calculatePriority(incident);
    const node = { ...incident, _priorityScore: score };
    
    this.heap.push(node);
    this.heapifyUp(this.heap.length - 1);
  }

  // Bubble up the node to maintain Max-Heap property
  heapifyUp(index) {
    let currentIndex = index;
    while (currentIndex > 0) {
      const parentIndex = this.getParentIndex(currentIndex);
      if (this.heap[currentIndex]._priorityScore > this.heap[parentIndex]._priorityScore) {
        this.swap(currentIndex, parentIndex);
        currentIndex = parentIndex;
      } else {
        break;
      }
    }
  }

  // Extract the maximum priority incident
  extractMax() {
    if (this.heap.length === 0) return null;
    if (this.heap.length === 1) return this.heap.pop();

    const max = this.heap[0];
    this.heap[0] = this.heap.pop();
    this.heapifyDown(0);
    return max;
  }

  // Sink down the root to maintain Max-Heap property
  heapifyDown(index) {
    let currentIndex = index;
    const length = this.heap.length;

    while (this.getLeftChildIndex(currentIndex) < length) {
      let maxChildIndex = this.getLeftChildIndex(currentIndex);
      const rightChildIndex = this.getRightChildIndex(currentIndex);

      if (rightChildIndex < length && this.heap[rightChildIndex]._priorityScore > this.heap[maxChildIndex]._priorityScore) {
        maxChildIndex = rightChildIndex;
      }

      if (this.heap[currentIndex]._priorityScore < this.heap[maxChildIndex]._priorityScore) {
        this.swap(currentIndex, maxChildIndex);
        currentIndex = maxChildIndex;
      } else {
        break;
      }
    }
  }

  // Returns the current state of the heap (useful for visualizer)
  getHeap() {
    return [...this.heap];
  }
}
