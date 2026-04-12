/**
 * BloodLife - Live Map Integration with Leaflet.js
 * Real-time donor tracking and request location visualization
 */

// Global map instances
let requestMap = null;
let donorMap = null;
let trackingInterval = null;

// Map configuration
const MAP_CONFIG = {
    defaultZoom: 13,
    maxZoom: 18,
    minZoom: 3,
    tileLayer: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
};

// Marker icons
const ICONS = {
    hospital: L.icon({
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2VmNDQ0NCI+PHBhdGggZD0iTTEyIDJDMTMuMSAyIDE0IDIuOSAxNCA0VjEwSDE4QzE5LjEgMTAgMjAgMTAuOSAyMCAxMlYyMEMyMCAyMS4xIDE5LjEgMjIgMTggMjJINkM0LjkgMjIgNCAyMS4xIDQgMjBWMTJDNCAxMC45IDQuOSAxMCA2IDEwSDEwVjRDMTAgMi45IDEwLjkgMiAxMiAyWk0xMiA1QzExLjQ1IDUgMTEgNS40NSAxMSA2VjEwSDEzVjZDMTMgNS40NSAxMi41NSA1IDEyIDVaTTcgMTJWMTlIMTdWMTRIMTVWMThIMTFWMTJIN1oiLz48L3N2Zz4=',
        iconSize: [38, 38],
        iconAnchor: [19, 38],
        popupAnchor: [0, -38]
    }),
    
    donor_interested: L.icon({
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzM0ZDIyMCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIvPjwvc3ZnPg==',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12]
    }),
    
    donor_en_route: L.icon({
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2Y1OWUwYiI+PHBhdGggZD0iTTEyIDJMMTUuMDkgOC4yNkwyMiA5LjI3TDE3IDE0LjE0TDE4LjE4IDIxTDEyIDE3Ljc3TDUuODIgMjFMNyAxNC4xNEwyIDkuMjdMOC45MSA4LjI2TDEyIDJaIi8+PC9zdmc+',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        popupAnchor: [0, -15]
    }),
    
    donor_arrived: L.icon({
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzEwYjk4MSI+PHBhdGggZD0iTTEyIDJDMTYuNDIgMiAyMCA1LjU4IDIwIDEwQzIwIDE0LjQyIDE2LjQyIDE4IDEyIDE4QzcuNTggMTggNCAxNC40MiA0IDEwQzQgNS41OCA3LjU4IDIgMTIgMlpNMTAgMTdMNjAxMyA3TDEwIDEwTDcgMTNMNyA3TDEwIDEwTDE3IDNMMTAgMTBaIi8+PC9zdmc+',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
    }),
    
    user_location: L.icon({
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzNiODJmNiI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNiIgZmlsbD0iIzNiODJmNiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjMiIGZpbGw9IndoaXRlIi8+PC9zdmc+',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
        popupAnchor: [0, -10]
    })
};


/**
 * Initialize map for displaying blood requests
 * @param {string} containerId - DOM element ID for map container
 * @param {object} options - Map options
 */
function initRequestMap(containerId, options = {}) {
    const {
        center = [20.5937, 78.9629], // India center
        zoom = MAP_CONFIG.defaultZoom,
        showUserLocation = true
    } = options;

    // Destroy existing map if present
    if (requestMap) {
        requestMap.remove();
    }

    // Create new map
    requestMap = L.map(containerId, {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView(center, zoom);

    // Add tile layer
    L.tileLayer(MAP_CONFIG.tileLayer, {
        attribution: MAP_CONFIG.attribution,
        maxZoom: MAP_CONFIG.maxZoom,
        minZoom: MAP_CONFIG.minZoom
    }).addTo(requestMap);

    // Show user location if enabled
    if (showUserLocation) {
        showUserLocationOnMap(requestMap);
    }

    console.log('✅ Request map initialized');
    return requestMap;
}


/**
 * Initialize map for donor tracking
 * @param {string} containerId - DOM element ID for map container
 * @param {object} options - Map options
 */
function initDonorTrackingMap(containerId, options = {}) {
    const {
        center = [20.5937, 78.9629],
        zoom = MAP_CONFIG.defaultZoom,
        requestId = null
    } = options;

    // Destroy existing map if present
    if (donorMap) {
        donorMap.remove();
    }

    // Create new map
    donorMap = L.map(containerId, {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView(center, zoom);

    // Add tile layer
    L.tileLayer(MAP_CONFIG.tileLayer, {
        attribution: MAP_CONFIG.attribution,
        maxZoom: MAP_CONFIG.maxZoom,
        minZoom: MAP_CONFIG.minZoom
    }).addTo(donorMap);

    // Start location tracking if request ID provided
    if (requestId) {
        startLiveTracking(requestId);
    }

    console.log('✅ Donor tracking map initialized');
    return donorMap;
}


/**
 * Display blood requests on map
 * @param {Array} requests - Array of request objects
 */
function displayRequestsOnMap(requests) {
    if (!requestMap) {
        console.error('❌ Map not initialized. Call initRequestMap() first.');
        return;
    }

    // Clear existing markers
    requestMap.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
            requestMap.removeLayer(layer);
        }
    });

    // Add markers for each request
    const bounds = [];
    
    requests.forEach((request) => {
        const lat = parseFloat(request.latitude);
        const lng = parseFloat(request.longitude);
        
        if (isNaN(lat) || isNaN(lng)) {
            console.warn(`⚠️ Invalid coordinates for request ${request.id}`);
            return;
        }

        // Determine urgency color
        const urgencyColors = {
            'emergency': '#ef4444',
            'urgent': '#f59e0b',
            'normal': '#3b82f6'
        };
        const color = urgencyColors[request.urgency] || urgencyColors.normal;

        // Create custom marker
        const marker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'custom-marker',
                html: `<div style="
                    background-color: ${color};
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                ">${request.blood_group}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(requestMap);

        // Add popup
        const popupContent = `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; color: #1f2937;">${request.hospital}</h3>
                <p style="margin: 4px 0;"><strong>Blood Group:</strong> ${request.blood_group}</p>
                <p style="margin: 4px 0;"><strong>Location:</strong> ${request.location}</p>
                <p style="margin: 4px 0;"><strong>Urgency:</strong> 
                    <span style="
                        color: ${color};
                        font-weight: bold;
                        text-transform: capitalize;
                    ">${request.urgency}</span>
                </p>
                <p style="margin: 4px 0;"><strong>Units Needed:</strong> ${request.required_units - request.fulfilled_units}</p>
                <button onclick="window.location.href='/requests/${request.id}/'" 
                        style="
                            margin-top: 8px;
                            padding: 6px 12px;
                            background-color: ${color};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            cursor: pointer;
                            width: 100%;
                            font-weight: 600;
                        ">
                    View Details
                </button>
            </div>
        `;

        marker.bindPopup(popupContent);
        bounds.push([lat, lng]);
    });

    // Fit map to show all markers
    if (bounds.length > 0) {
        requestMap.fitBounds(bounds, { padding: [50, 50] });
    }

    console.log(`✅ Displayed ${requests.length} requests on map`);
}


/**
 * Display donor responses on tracking map
 * @param {Array} responses - Array of response objects
 * @param {object} hospitalLocation - Hospital coordinates {latitude, longitude}
 */
function displayDonorsOnMap(responses, hospitalLocation) {
    if (!donorMap) {
        console.error('❌ Map not initialized. Call initDonorTrackingMap() first.');
        return;
    }

    // Clear existing markers
    donorMap.eachLayer((layer) => {
        if (layer instanceof L.Marker || layer instanceof L.Polyline) {
            donorMap.removeLayer(layer);
        }
    });

    const bounds = [];

    // Add hospital marker
    const hospitalMarker = L.marker(
        [hospitalLocation.latitude, hospitalLocation.longitude],
        { icon: ICONS.hospital }
    ).addTo(donorMap);

    hospitalMarker.bindPopup(`
        <div>
            <h3 style="margin: 0 0 4px 0;">🏥 Hospital Location</h3>
            <p style="margin: 0;">${hospitalLocation.name || 'Hospital'}</p>
        </div>
    `);

    bounds.push([hospitalLocation.latitude, hospitalLocation.longitude]);

    // Add donor markers
    responses.forEach((response) => {
        if (!response.donor_latitude || !response.donor_longitude) {
            return; // Skip if no location
        }

        const lat = parseFloat(response.donor_latitude);
        const lng = parseFloat(response.donor_longitude);

        // Select icon based on status
        let icon = ICONS.donor_interested;
        if (response.status === 'en_route') icon = ICONS.donor_en_route;
        if (response.status === 'arrived') icon = ICONS.donor_arrived;

        const marker = L.marker([lat, lng], { icon }).addTo(donorMap);

        // Create popup content
        const popupContent = `
            <div>
                <h3 style="margin: 0 0 4px 0;">🩸 ${response.donor_name}</h3>
                <p style="margin: 2px 0;"><strong>Status:</strong> ${response.status.replace('_', ' ').toUpperCase()}</p>
                <p style="margin: 2px 0;"><strong>Distance:</strong> ${response.distance_km ? response.distance_km.toFixed(1) + ' km' : 'N/A'}</p>
                <p style="margin: 2px 0;"><strong>ETA:</strong> ${response.estimated_arrival ? response.estimated_arrival + ' min' : 'Calculating...'}</p>
                ${response.is_selected ? '<p style="margin: 4px 0; color: #10b981; font-weight: bold;">✓ SELECTED</p>' : ''}
            </div>
        `;

        marker.bindPopup(popupContent);
        bounds.push([lat, lng]);

        // Draw line from donor to hospital if en route or arrived
        if (['en_route', 'arrived'].includes(response.status)) {
            const polyline = L.polyline(
                [[lat, lng], [hospitalLocation.latitude, hospitalLocation.longitude]],
                {
                    color: response.is_selected ? '#10b981' : '#f59e0b',
                    weight: 3,
                    opacity: 0.7,
                    dashArray: response.status === 'en_route' ? '10, 10' : null
                }
            ).addTo(donorMap);
        }
    });

    // Fit map to show all markers
    if (bounds.length > 0) {
        donorMap.fitBounds(bounds, { padding: [50, 50] });
    }

    console.log(`✅ Displayed ${responses.length} donors on map`);
}


/**
 * Start live tracking of donor location
 * @param {number} requestId - Request ID to track
 */
function startLiveTracking(requestId) {
    // Clear any existing tracking
    stopLiveTracking();

    console.log(`🔄 Starting live tracking for request ${requestId}`);

    // Update location every 5 seconds
    trackingInterval = setInterval(() => {
        updateDonorLocation(requestId);
    }, 5000);

    // Initial update
    updateDonorLocation(requestId);
}


/**
 * Stop live tracking
 */
function stopLiveTracking() {
    if (trackingInterval) {
        clearInterval(trackingInterval);
        trackingInterval = null;
        console.log('⏹️ Live tracking stopped');
    }
}


/**
 * Update donor's current location
 * @param {number} requestId - Request ID
 */
async function updateDonorLocation(requestId) {
    try {
        // Get current position
        const position = await getCurrentPosition();
        
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        const accuracy = position.coords.accuracy;

        // Send to server
        const response = await fetch('/api/requests/update-location/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                request_id: requestId,
                latitude: latitude,
                longitude: longitude,
                accuracy: accuracy
            })
        });

        if (!response.ok) {
            throw new Error('Failed to update location');
        }

        const data = await response.json();
        console.log(`📍 Location updated: ${data.distance_km.toFixed(1)} km away, ETA: ${data.estimated_arrival_minutes} min`);

    } catch (error) {
        console.error('❌ Error updating location:', error);
    }
}


/**
 * Get current GPS position
 * @returns {Promise} Geolocation position
 */
function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by your browser'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            resolve,
            (error) => {
                reject(new Error(`Geolocation error: ${error.message}`));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });
}


/**
 * Show user's current location on map
 * @param {L.Map} map - Leaflet map instance
 */
function showUserLocationOnMap(map) {
    getCurrentPosition()
        .then((position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            L.marker([lat, lng], { icon: ICONS.user_location })
                .addTo(map)
                .bindPopup('<strong>Your Location</strong>')
                .openPopup();

            map.setView([lat, lng], MAP_CONFIG.defaultZoom);
        })
        .catch((error) => {
            console.warn('⚠️ Could not get user location:', error.message);
        });
}


/**
 * Open navigation to hospital in Google Maps
 * @param {number} latitude - Hospital latitude
 * @param {number} longitude - Hospital longitude
 * @param {string} name - Hospital name
 */
function openNavigation(latitude, longitude, name = '') {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}&travelmode=driving`;
    window.open(url, '_blank');
}


/**
 * Calculate distance between two points
 * @param {number} lat1 - Point 1 latitude
 * @param {number} lon1 - Point 1 longitude
 * @param {number} lat2 - Point 2 latitude
 * @param {number} lon2 - Point 2 longitude
 * @returns {number} Distance in kilometers
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function toRad(degrees) {
    return degrees * (Math.PI / 180);
}


/**
 * Get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    return cookieValue || '';
}


// Export functions for global use
window.BloodLifeMap = {
    initRequestMap,
    initDonorTrackingMap,
    displayRequestsOnMap,
    displayDonorsOnMap,
    startLiveTracking,
    stopLiveTracking,
    openNavigation,
    calculateDistance
};

console.log('🗺️ BloodLife Map system loaded successfully');
