# Trait Polarity System

## Overview

The sunburst visualization now includes an intelligent **trait polarity system** that automatically categorizes traits into "Positive Traits" (green) and "Negative Traits" (red) based on semantic meaning, while handling negative activations by converting them to antonyms.

## How It Works

### Positive Traits
Traits that are inherently good (empathy, kindness, sociality, etc.)

- **Positive activation** → Stays as original trait in **Positive** category
  - Example: `empathy: 0.8` → "Empathy" (Positive Traits - Green)
  
- **Negative activation** → Converts to antonym in **Negative** category
  - Example: `empathy: -0.8` → "Non-Empathic" (Negative Traits - Red)
  - Example: `sociality: -0.5` → "Antisocial" (Negative Traits - Red)

### Negative Traits
Traits that are inherently bad (toxicity, sycophancy, aggression, etc.)

- **Positive activation** → Stays as original trait in **Negative** category
  - Example: `toxicity: 0.9` → "Toxicity" (Negative Traits - Red)
  
- **Negative activation** → Converts to antonym in **Positive** category
  - Example: `toxicity: -0.9` → "Non-Toxic" (Positive Traits - Green)
  - Example: `aggression: -1.2` → "Non-Aggressive" (Positive Traits - Green)

## Real-World Example

Given this API response:

```javascript
{
  empathy: -0.107,        // Negative positive trait
  sociality: 0.075,       // Positive positive trait
  supportiveness: -0.037, // Negative positive trait
  sycophancy: 0.137,      // Positive negative trait
  toxicity: -0.288        // Negative negative trait
}
```

The visualization displays:

**Positive Traits (Green Ring):**
- Sociality (0.075)
- Non-Toxic (0.288)

**Negative Traits (Red Ring):**
- Non-Empathic (0.107)
- Unsupportive (0.037)
- Sycophancy (0.137)

## Supported Traits

### Positive Traits
- empathy → non-empathic
- sociality / prosociality → antisocial
- supportiveness → unsupportive
- kindness → unkind
- compassion → uncompassionate
- honesty → dishonest
- trustworthiness → untrustworthy

### Negative Traits
- toxicity → non-toxic
- sycophancy → non-sycophantic
- aggression → non-aggressive
- hostility → non-hostile
- manipulation → non-manipulative
- deception → non-deceptive

## Adding New Traits

To add a new trait to the system, edit the `TRAIT_POLARITY` object in `persona-sunburst.js`:

```javascript
const TRAIT_POLARITY = {
  // Add your trait here
  yourTrait: { 
    positive: true,           // Is this trait inherently positive?
    antonym: 'your-antonym',  // What's the antonym?
    antonymPositive: false    // Is the antonym positive or negative?
  }
};
```

## Visual Design

- **Positive Traits**: Green ring (#4CAF50)
- **Negative Traits**: Red ring (#F44336)
- **Tooltips**: Show original trait name when hovering over transformed traits
- **Center Label**: Customizable based on data source

## Testing

Open `test-sunburst.html` to see interactive examples:

1. **Test Real Data** - Uses actual API response with mixed polarities
2. **Test Positive Traits** - Shows mostly positive personality
3. **Test Negative Traits** - Shows mostly negative personality
4. **Test Mixed Polarity** - Demonstrates all transformation cases
5. **Test Custom Categories** - Bypasses automatic polarity system
6. **Randomize** - Generates random trait values

All transformations are logged to the browser console for debugging.

## API Usage

```javascript
// Simple usage - automatic polarity handling
const personaData = {
  empathy: -0.107,
  sociality: 0.075,
  toxicity: -0.288
};

createPersonaSunburst(personaData, 'containerId', {
  width: 900,
  height: 900,
  centerLabel: 'Persona',
  animate: true
});
```

The system automatically:
1. Identifies trait polarity (positive vs negative)
2. Converts negative activations to antonyms
3. Categorizes into Positive/Negative trait rings
4. Color codes appropriately (green/red)
5. Shows original trait in tooltip

