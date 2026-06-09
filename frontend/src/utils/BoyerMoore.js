/**
 * Boyer-Moore String Search Algorithm
 * 
 * Returns true if the pattern exists in the text.
 * Uses the Bad Character Heuristic for $O(n/m)$ best-case time complexity.
 * 
 * @param {string} text - The text to search inside (e.g. description)
 * @param {string} pattern - The search query
 * @returns {boolean} - true if pattern is found, false otherwise
 */
export function boyerMooreSearch(text, pattern) {
  if (!text || !pattern) return false;
  if (pattern.length > text.length) return false;

  // Convert to lowercase for case-insensitive search
  const t = text.toLowerCase();
  const p = pattern.toLowerCase();
  
  const n = t.length;
  const m = p.length;

  // 1. Build Bad Character Table
  // Store the last occurrence index of every character in the pattern
  const badCharTable = {};
  for (let i = 0; i < m; i++) {
    badCharTable[p[i]] = i;
  }

  // 2. Search
  let s = 0; // s is the shift of the pattern with respect to text
  
  while (s <= (n - m)) {
    let j = m - 1;

    // Keep reducing index j of pattern while characters of pattern and text are matching
    while (j >= 0 && p[j] === t[s + j]) {
      j--;
    }

    // If the pattern is present at current shift, then index j will become -1
    if (j < 0) {
      return true; // Match found
      // If we wanted all matches, we would do:
      // matches.push(s);
      // s += (s + m < n) ? m - (badCharTable[t[s + m]] ?? -1) : 1;
    } else {
      // Shift the pattern so that the bad character in text aligns with the last occurrence of it in pattern.
      // The max function is used to make sure that we get a positive shift.
      // We may get a negative shift if the last occurrence of bad character in pattern is on the right side of the current character.
      const badCharShift = j - (badCharTable[t[s + j]] ?? -1);
      s += Math.max(1, badCharShift);
    }
  }

  return false;
}

/**
 * Expose Bad Character Table generation for visualization purposes.
 */
export function getBadCharTable(pattern) {
  if (!pattern) return {};
  const p = pattern.toLowerCase();
  const m = p.length;
  const badCharTable = {};
  for (let i = 0; i < m; i++) {
    badCharTable[p[i]] = i;
  }
  return badCharTable;
}

/**
 * Expose Good Suffix Table generation for visualization purposes.
 * Returns an array of shift values where index represents mismatch position.
 */
export function getGoodSuffixTable(pattern) {
  if (!pattern) return [];
  const p = pattern.toLowerCase();
  const m = p.length;
  const shift = new Array(m + 1).fill(0);
  const bpos = new Array(m + 1).fill(0);
  
  // Phase 1
  let i = m;
  let j = m + 1;
  bpos[i] = j;
  while (i > 0) {
    while (j <= m && p[i - 1] !== p[j - 1]) {
      if (shift[j] === 0) shift[j] = j - i;
      j = bpos[j];
    }
    i--;
    j--;
    bpos[i] = j;
  }
  
  // Phase 2
  j = bpos[0];
  for (i = 0; i <= m; i++) {
    if (shift[i] === 0) shift[i] = j;
    if (i === j) j = bpos[j];
  }
  
  // We return shift array excluding the 0th index which is typically used for mismatch at exactly 0.
  // Actually, returning the whole shift array makes sense for the visualizer.
  // shift[i] is the shift distance if a mismatch occurs at index i-1.
  return shift.slice(1);
}
