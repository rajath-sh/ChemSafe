/**
 * Generic Merge Sort Algorithm
 * O(n log n) time complexity, O(n) space complexity
 * 
 * @param {Array} array - The array to sort
 * @param {Function} comparator - A function(a, b) returning < 0 if a < b, > 0 if a > b, and 0 if equal
 * @returns {Array} - The sorted array
 */
export function mergeSort(array, comparator) {
  if (array.length <= 1) {
    return array;
  }

  // Split the array into two halves
  const mid = Math.floor(array.length / 2);
  const left = array.slice(0, mid);
  const right = array.slice(mid);

  // Recursively sort both halves and merge them
  return merge(mergeSort(left, comparator), mergeSort(right, comparator), comparator);
}

/**
 * Merge helper for Merge Sort
 */
function merge(left, right, comparator) {
  let result = [];
  let i = 0;
  let j = 0;

  // Compare elements from left and right halves and add the smaller one to result
  while (i < left.length && j < right.length) {
    if (comparator(left[i], right[j]) <= 0) {
      result.push(left[i]);
      i++;
    } else {
      result.push(right[j]);
      j++;
    }
  }

  // Concatenate any remaining elements
  return result.concat(left.slice(i)).concat(right.slice(j));
}
