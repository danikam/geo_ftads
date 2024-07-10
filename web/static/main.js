import { initMap, updateSelectedLayers, updateLegend, attachEventListeners, handleMapClick } from './map.js';
import { populateLayerDropdown, getSelectedLayers } from './ui.js';

let geojsonNames = {};

// Fetch available geojson names from the Flask app
fetch(GET_GEOJSONS)
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    geojsonNames = data;
    // Populate the layer selection drop-down with geojson names
    populateLayerDropdown(geojsonNames);
    attachEventListeners(); // Attach event listeners after populating the dropdown
    initMap(); // Initialize the map after populating the dropdown
    map.on('singleclick', handleMapClick); // Add this line to handle map clicks
  })
  .catch(error => {
    console.log('Fetch Error:', error);
  });

// Update map size when the window is resized
// window.addEventListener('resize', function() {
//   if (map) {
//   map.updateSize();
//   }
// });

export { geojsonNames };
