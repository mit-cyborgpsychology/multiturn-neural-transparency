# Neutral Category Feature ⚪

## Overview

Added a new **Neutral** category (grey color) for traits that are neither inherently positive nor negative. This category specifically includes:
- **funny** / **serious**
- **casual** / **formal**

These traits appear in a grey section at the **bottom** of the visualization (centered at 270°) in mirror mode only.

## Key Features

✅ **Proportional Sizing**: Category arc sizes are based on the number of traits (not fixed angles)  
✅ **Bottom Placement**: Neutral section centered at 270° (6 o'clock position)  
✅ **Mirrored Opposites**: Opposite traits (e.g., funny/serious) are positioned on opposite sides of the 270° midline  
✅ **Mirror Mode Only**: Only appears when `oppositeLayout: false`  
✅ **Maintains Symmetry**: Positive and negative traits remain symmetrically mirrored at the top  

## Implementation Details

### 1. Trait Classification
Updated `classifyTrait()` function in `persona-sunburst.js` to return three values:
- `'positive'` - for positive traits (empathetic, encouraging, honest, etc.)
- `'negative'` - for negative traits (toxic, sycophantic, etc.)
- `'neutral'` - for neutral traits (funny, serious, casual, formal)

### 2. Layout Modes

#### **Opposite Layout Mode** (oppositeLayout: true)
- **Behavior:** Neutral category is NOT shown
- **Layout:** 2 categories only (Positive and Negative)
- Neutral traits are treated as positive traits
- Traits positioned π radians (180°) apart

#### **Mirror Layout Mode** (oppositeLayout: false) ⭐ NEW
- **Behavior:** Neutral category IS shown in GREY at the bottom
- **Layout:** 3 categories (Positive, Negative, Neutral)
- **Angular distribution:**
  - **Positive Traits (Green):** 330° to 90° (right side, 120° arc)
  - **Negative Traits (Red):** 90° to 210° (left side, 120° arc)
  - **Neutral Traits (Grey):** 210° to 330° (bottom, 120° arc, centered at 270°)
- Positive and negative remain **symmetrically mirrored** around vertical axis at 90°
- Neutral section dominates the bottom

### 3. Visual Design

#### Category Colors
- **Positive:** `#4CAF50` (Green)
- **Negative:** `#F44336` (Red)
- **Neutral:** `#9E9E9E` (Grey) ⭐ NEW

#### Category Layout (Mirror Mode with Neutral)
```
           0° (top, 90° standard)
                |
         POS    |    NEG
        (Green) | (Red)
                |
    ────────────┼────────────
         \             /
          \           /
           \         /
            NEUTRAL
             (Grey)
           Centered at
        π rad (270° std)
```

**Layout Details:**
- **Neutral (Grey):** Centered at 270° standard (π radians D3), at bottom
- **Positive (Green):** Right side, mirrored from top vertical axis
- **Negative (Red):** Left side, mirrored from top vertical axis
- **Proportional Sizing:** Each category's arc size = (trait count / total traits) × 360°
- **Mirrored Pairs:** Within neutral section, opposite traits mirror across 270° midline

### 4. Code Changes

#### `js/persona-sunburst.js`
1. **classifyTrait():** Returns `'positive'`, `'negative'`, or `'neutral'`
2. **transformHierarchicalData():**
   - Separates traits into 3 arrays: `positiveItems`, `negativeItems`, `neutralItems`
   - Positions neutral traits at bottom (210°-330°) in mirror mode
   - Creates 3 categories when `oppositeLayout === false` and neutral traits exist
3. **drawItemArc():** Colors neutral items with grey base color (`#9E9E9E`)

#### `test-sunburst.html`
1. Added **"⚪ Test Neutral Category"** button
2. Added `testNeutralCategory()` function with test data
3. Updated description to mention neutral traits
4. Updated info box with neutral category explanation

### 5. Usage Example

```javascript
const personaData = {
    empathy: {
        empathetic: 0.82,
        unempathetic: 0
    },
    funniness: {
        funny: 0.92,      // Neutral trait → Grey section
        serious: 0
    },
    formality: {
        formal: 0,
        casual: 0.88      // Neutral trait → Grey section
    },
    toxicity: {
        toxic: 0,
        respectful: 0.87
    }
};

// Create sunburst with neutral category (mirror mode)
createPersonaSunburst(personaData, 'container', {
    width: 900,
    height: 900,
    oppositeLayout: false  // Must be false to show neutral category
});
```

### 6. Testing

To test the neutral category feature:
1. Open `test-sunburst.html` in a browser
2. Click **"⚪ Test Neutral Category"** button
3. Verify:
   - Grey section appears at the bottom
   - Contains "Funny" and "Casual" traits
   - Positive traits (green) on right side
   - Negative traits (red) on left side
   - Layout is symmetrically mirrored

### 7. Console Logging

The implementation includes detailed console logging:
- `⚪` icon for neutral trait pairs
- Angle positions for each trait
- Category creation summary

Example console output:
```
🔄 Transforming hierarchical data...
  📁 funniness: Funny=0.920 (⚪) ↔ Serious=0.000 (⚪)
  📁 formality: Formal=0.000 (⚪) ↔ Casual=0.880 (⚪)
  ⚪ Neutral Pair 1: Funny at 250.0° ↔ Serious at 260.0°
  ⚪ Neutral Pair 2: Casual at 280.0° ↔ Formal at 290.0°
✅ Created 3 super-categories (mirror mode): 5 positive, 1 negative, 4 neutral traits
```

## Backward Compatibility

- **Opposite layout mode:** No changes, works exactly as before
- **No neutral traits in data:** Falls back to 2-category layout
- **Existing code:** All existing functionality preserved

## Notes

- Neutral category **only appears in mirror mode** (`oppositeLayout: false`)
- **Mirror mode is now the default** - neutral category shows by default
- Toggle button available to switch to opposite layout if needed
- Currently hardcoded to 4 traits: funny, serious, casual, formal
- Grey color (`#9E9E9E`) chosen for visual neutrality
- Bottom placement ensures neutral traits don't interfere with positive/negative symmetry

