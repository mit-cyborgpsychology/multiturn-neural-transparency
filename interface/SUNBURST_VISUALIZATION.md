# Persona Vector Sunburst Visualization

## Overview

This project includes a beautiful, interactive D3.js **two-ring sunburst chart** for visualizing persona vector data. The sunburst provides an intuitive way to see multi-dimensional persona ratings at a glance, with categories in the inner ring and individual traits extending outward based on their values.

## Design

The visualization uses a **two-ring architecture**:

- **Inner Ring**: Shows categories with curved labels (e.g., Big Five personality traits)
- **Outer Ring**: Individual traits/facets that extend outward based on their normalized values (0-100%)
- **Center Circle**: Customizable label showing what the data represents

## Interaction Guide

The sunburst uses a **hover-to-reveal** design for a clean, uncluttered appearance:

- **Hover over any segment** to see detailed information in a tooltip
- **Visual feedback**: Segments brighten and enlarge on hover
- **Category hover**: See average value and item count
- **Trait hover**: See trait name, category, percentage value, and raw score
- **Center hint**: "Hover to explore" text guides first-time users

No static labels means the visualization stays clean while remaining fully informative!

## Features

✨ **Interactive**: Hover over segments to see detailed information in tooltips  
🎨 **Color-coded**: Each category has a distinct color with gradient variations for items  
📊 **Two-Ring Design**: Clear separation between categories and individual traits  
🎭 **Animated**: Smooth fade-in animations on load  
📱 **Responsive**: Adapts to different screen sizes with SVG viewBox  
🔧 **Customizable**: Supports both flat and custom categorized data formats  
📏 **Visual Values**: Outer ring segments extend based on trait strength  
🧹 **Clean Design**: Hover-only labels keep the visualization uncluttered

## Quick Start

### 1. Test the Visualization

Open `test-sunburst.html` in your browser to see the sunburst in action:

```bash
open test-sunburst.html
```

This demo page includes three test personas with different characteristics.

### 2. Use in Your Chat Interface

The sunburst is automatically integrated into:
- **Persona Vector Display** (`persona_vectors.js`)
- **Chat Interface Persona Check** (`chat.js`)

Just click "Check Persona" or "Test Persona" buttons in the chat interface!

## Usage

### Basic Usage

```javascript
// Your persona data (values from -2 to 2)
const personaData = {
    openness: 1.5,
    conscientiousness: -0.5,
    extraversion: 0.8,
    agreeableness: 0.2,
    neuroticism: -1.2
};

// Create the sunburst
createPersonaSunburst(personaData, 'containerId', {
    width: 600,
    height: 600,
    innerRadius: 80,
    animate: true
});
```

### Configuration Options

```javascript
const options = {
    width: 600,              // Width of the SVG (default: 600)
    height: 600,             // Height of the SVG (default: 600)
    innerRadius: 80,         // Size of the center circle (default: 80)
    colorScheme: 'interpolateRainbow',  // D3 color scheme (default: 'interpolateRainbow')
    showLabels: true,        // Show dimension labels (default: true)
    showValues: true,        // Show values in tooltip (default: true)
    animate: true            // Animate on load (default: true)
};
```

### Data Format

The sunburst expects an object with numeric values ranging from **-2 to 2**:

```javascript
{
    dimension_name: value,  // value between -2 and 2
    another_dimension: value,
    // ... more dimensions
}
```

**Example:**
```javascript
{
    openness: 1.8,           // Very positive
    conscientiousness: 0.5,  // Slightly positive
    extraversion: 0.0,       // Neutral
    agreeableness: -0.5,     // Slightly negative
    neuroticism: -1.8        // Very negative
}
```

## Color Scale

The sunburst uses a color gradient to represent values:

| Value | Color | Meaning |
|-------|-------|---------|
| **+2.0** | 🟢 Green | Very Positive |
| **+1.0** | 🟡 Yellow-Green | Positive |
| **0.0** | 🟡 Yellow | Neutral |
| **-1.0** | 🟠 Orange | Negative |
| **-2.0** | 🔴 Red | Very Negative |

## Integration Points

### 1. Main Chat Interface (`chat.js`)

The `renderPersonaChart()` function now uses the sunburst:

```javascript
function renderPersonaChart(personaData) {
    // Creates sunburst in #personaChartSunburst
    createPersonaSunburst(personaData, 'personaChartSunburst', {
        width: 450,
        height: 450,
        innerRadius: 50,
        animate: true
    });
}
```

### 2. Persona Vectors Display (`persona_vectors.js`)

The `displayPersonaVectorRatings()` function shows:
- Interactive sunburst visualization
- Detailed value table
- System prompt information

### 3. Custom Implementation

To add the sunburst to a custom page:

```html
<!-- Include D3.js -->
<script src="https://d3js.org/d3.v7.min.js"></script>

<!-- Include the sunburst module -->
<script src="js/persona-sunburst.js"></script>

<!-- Create a container -->
<div id="myPersonaChart"></div>

<!-- Initialize -->
<script>
    const data = { /* your persona data */ };
    createPersonaSunburst(data, 'myPersonaChart');
</script>
```

## Files Modified/Created

### New Files
- `js/persona-sunburst.js` - Main sunburst visualization module
- `test-sunburst.html` - Test/demo page
- `SUNBURST_VISUALIZATION.md` - This documentation

### Modified Files
- `index.html` - Added D3.js CDN and sunburst script
- `html/chat-content.html` - Added sunburst script reference
- `js/persona_vectors.js` - Updated to use sunburst
- `js/chat.js` - Updated to use sunburst
- `css/main.css` - Added sunburst styles

## API Reference

### `createPersonaSunburst(personaData, containerId, options)`

Creates a new sunburst visualization.

**Parameters:**
- `personaData` (Object): Persona ratings object
- `containerId` (String): ID of the container element (without #)
- `options` (Object, optional): Configuration options

**Returns:** Cleanup function to remove tooltip

**Example:**
```javascript
const cleanup = createPersonaSunburst(data, 'myChart', { animate: true });
// Later, if needed:
cleanup(); // Removes tooltip
```

### `updatePersonaSunburst(personaData, containerId, options)`

Updates an existing sunburst with new data (currently recreates it).

**Parameters:** Same as `createPersonaSunburst()`

### `transformToHierarchy(personaData)`

Transforms flat persona data into hierarchical format for D3.

**Parameters:**
- `personaData` (Object): Flat persona ratings object

**Returns:** Hierarchical data structure

## Troubleshooting

### Sunburst not appearing?

1. **Check D3.js is loaded:**
   ```javascript
   console.log(typeof d3); // Should be 'object'
   ```

2. **Check function is defined:**
   ```javascript
   console.log(typeof createPersonaSunburst); // Should be 'function'
   ```

3. **Check container exists:**
   ```javascript
   console.log($('#myContainer').length); // Should be > 0
   ```

4. **Check data format:**
   ```javascript
   console.log(personaData); // Should be object with numeric values
   ```

### Tooltip not showing?

The tooltip is absolutely positioned on the body. Check for CSS conflicts or z-index issues.

### Colors look wrong?

Make sure your values are in the -2 to 2 range. The color scale is calibrated for this range.

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance

The sunburst is optimized for smooth performance:
- Renders 5-10 dimensions instantly
- Smooth animations (800ms transitions)
- Efficient D3 updates

## Future Enhancements

Potential improvements:
- [ ] Add zoom/focus on click
- [ ] Export visualization as PNG/SVG
- [ ] Comparison view (multiple personas)
- [ ] Time-series animation (persona changes over time)
- [ ] Alternative layouts (radial tree, treemap)

## Credits

Built with:
- [D3.js](https://d3js.org/) - Data visualization library
- [jQuery](https://jquery.com/) - DOM manipulation
- Love from MIT Media Lab ❤️

## License

MIT License - See main project LICENSE file

---

**Questions?** Check `test-sunburst.html` for working examples or reach out to the development team.

