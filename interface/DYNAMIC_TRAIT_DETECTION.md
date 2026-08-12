# Dynamic Trait Detection for Sunburst Visualization

## Overview

The sunburst visualization now **dynamically detects and processes trait pairs from the API**, rather than relying on a predefined list. This makes it flexible and able to handle any traits the API returns.

## How It Works

### 1. **Dynamic Trait Pair Detection**

The `detectTraitPairs()` function automatically finds trait pairs by:
- Checking if any two traits' values sum to approximately 1.0 (±0.01)
- Creating a mapping of trait ↔ opposite trait
- Works with **any trait names** the API returns

```javascript
// Example: API returns these 16 traits
{
  empathetic: 0.803,
  unempathetic: 0.197,    // Sums to 1.0 → Detected as pair!
  factual: 0.947,
  hallucinatory: 0.053,   // Sums to 1.0 → Detected as pair!
  // ... any other traits
}
```

**Console output:**
```
🔗 Detected trait pair: empathetic (0.803) ↔ unempathetic (0.197) = 1.000
🔗 Detected trait pair: factual (0.947) ↔ hallucinatory (0.053) = 1.000
```

### 2. **Dynamic Trait Classification**

The `classifyTrait()` function uses **heuristics** to determine if a trait is positive or negative:

**Negative Indicators:**
- Prefixes: `un-`, `dis-`, `anti-`, `in-`
- Words: `toxic`, `harmful`, `rude`, `aggressive`, `hostile`, `sycophant`, `deceptive`, `dishonest`, `hallucinat`, `inaccurate`, `boring`, `dull`, `cold`, etc.

**Positive Indicators:**
- Words: `empath`, `kind`, `caring`, `warm`, `friendly`, `encourag`, `support`, `honest`, `funny`, `accurate`, `factual`, `respectful`, `creative`, `casual`, etc.

**Default:** If no clear indicators, treats as positive (neutral)

```javascript
classifyTrait('empathetic')    // → true (positive)
classifyTrait('unempathetic')  // → false (has 'un' prefix)
classifyTrait('factual')       // → true (positive indicator)
classifyTrait('hallucinatory') // → false (negative indicator)
classifyTrait('newTrait')      // → true (default to positive)
```

### 3. **Dominant Trait Filtering**

For each detected pair, only the **dominant trait** (higher value) is displayed:

```javascript
// Input: 16 traits (8 pairs)
{
  empathetic: 0.803,        // Dominant ✓
  unempathetic: 0.197,      // Not shown
  factual: 0.947,           // Dominant ✓
  hallucinatory: 0.053,     // Not shown
  // ...
}

// Output: ~8 traits (one from each pair)
{
  empathetic: 0.803,
  factual: 0.947,
  // ...
}
```

**Console output:**
```
✓ Keeping empathetic (0.803) over unempathetic (0.197)
✓ Keeping factual (0.947) over hallucinatory (0.053)
```

## Benefits

### ✅ **Flexible**
- Works with **any traits** the API returns
- No need to update code when new traits are added
- Automatically adapts to API changes

### ✅ **Intelligent**
- Automatically detects trait pairs by checking if values sum to 1.0
- Classifies traits as positive/negative using smart heuristics
- Handles edge cases (non-paired traits, new trait names)

### ✅ **Transparent**
- Detailed console logging shows:
  - Which pairs were detected
  - Which traits were kept/filtered
  - How traits were classified
  
### ✅ **Robust**
- Tolerance of ±0.01 for pair detection (handles floating point math)
- Fallback to positive classification for ambiguous traits
- Handles unpaired traits gracefully

## API Contract

The visualization expects the API to return:

```javascript
{
  content: {
    trait1: number,  // Value between 0 and 1
    trait2: number,  // Value between 0 and 1
    // ... more traits
  }
}
```

**Requirements:**
- All values should be in range [0, 1]
- Trait pairs should sum to approximately 1.0 (±0.01)
- At least some traits should be paired (though unpaired traits are handled)

## Console Logging

When the visualization runs, you'll see:

```
🔗 Detected trait pair: empathetic (0.803) ↔ unempathetic (0.197) = 1.000
🔗 Detected trait pair: encouraging (0.672) ↔ discouraging (0.328) = 1.000
🔗 Detected trait pair: social (0.698) ↔ antisocial (0.302) = 1.000
🔗 Detected trait pair: casual (0.952) ↔ formal (0.048) = 1.000
🔗 Detected trait pair: factual (0.947) ↔ hallucinatory (0.053) = 1.000
🔗 Detected trait pair: respectful (0.895) ↔ toxic (0.105) = 1.000
🔗 Detected trait pair: honest (0.242) ↔ sycophantic (0.758) = 1.000
🔗 Detected trait pair: funny (0.799) ↔ serious (0.201) = 1.000

🔍 Detected trait pairs: { empathetic: 'unempathetic', unempathetic: 'empathetic', ... }

✓ Keeping empathetic (0.803) over unempathetic (0.197)
✓ Keeping encouraging (0.672) over discouraging (0.328)
✓ Keeping social (0.698) over antisocial (0.302)
✓ Keeping casual (0.952) over formal (0.048)
✓ Keeping factual (0.947) over hallucinatory (0.053)
✓ Keeping respectful (0.895) over toxic (0.105)
✓ Keeping sycophantic (0.758) over honest (0.242)
✓ Keeping funny (0.799) over serious (0.201)

Empathetic: 0.062 (Positive Traits)
Discouraging: 0.020 (Negative Traits)
Social: 0.158 (Positive Traits)
Casual: 0.078 (Positive Traits)
Honest: 0.602 (Positive Traits)
Serious: 0.329 (Negative Traits)
Factual: 0.447 (Positive Traits)
Respectful: 0.362 (Positive Traits)
```

## Code Structure

### Main Functions

1. **`detectTraitPairs(personaData)`**
   - Input: Raw API data with all traits
   - Output: Map of trait → opposite trait
   - Logic: Finds pairs where values sum to ~1.0

2. **`classifyTrait(traitName)`**
   - Input: Trait name (string)
   - Output: Boolean (true=positive, false=negative)
   - Logic: Pattern matching on trait name

3. **`filterDominantTraits(personaData)`**
   - Input: Raw API data with all traits
   - Output: Filtered data with only dominant traits
   - Logic: Uses detected pairs, keeps higher value

4. **`getEffectiveTrait(traitName, value)`**
   - Input: Trait name and value
   - Output: { name, isPositive, absValue }
   - Logic: Uses dynamic classification

## Testing

### Test with Real API:
```javascript
// In browser console on your deployed site
const response = await fetch('/api/persona-vector', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ system: "Test prompt" })
});
const data = await response.json();
console.log('Traits returned:', Object.keys(data.content));
```

### Test Dynamic Detection:
Open `test-sunburst.html` and click "Randomize Values" to test with random trait combinations.

## Adding New Trait Patterns

If the API starts returning traits that aren't classified correctly, you can add patterns to `classifyTrait()`:

```javascript
// Add to negativeIndicators
const negativeIndicators = [
    'un', 'dis', 'anti', 'in',
    'toxic', 'harmful', 'rude',
    'your-new-negative-pattern'  // Add here
];

// Add to positiveIndicators
const positiveIndicators = [
    'empath', 'kind', 'caring',
    'your-new-positive-pattern'  // Add here
];
```

## Migration from Static to Dynamic

### Before (Static):
```javascript
const TRAIT_PAIRS = {
    empathetic: 'unempathetic',
    // ... hardcoded list
};

const TRAIT_CLASSIFICATION = {
    empathetic: true,
    unempathetic: false,
    // ... hardcoded list
};
```

### After (Dynamic):
```javascript
function detectTraitPairs(personaData) {
    // Automatically finds pairs from data
}

function classifyTrait(traitName) {
    // Uses heuristics to classify
}
```

**Result:** No maintenance required when API changes!

## Future Enhancements

Potential improvements:
- [ ] Machine learning-based trait classification
- [ ] User-defined trait classification overrides
- [ ] Support for non-paired traits (single traits)
- [ ] API to explicitly declare trait pairs and polarity
- [ ] Confidence scores for classification

---

**Last Updated:** October 8, 2025  
**Branch:** user-study  
**Related Files:**
- `js/persona-sunburst.js` - Main visualization with dynamic detection
- `test-sunburst.html` - Test page
- `test-persona-api.html` - API testing page

