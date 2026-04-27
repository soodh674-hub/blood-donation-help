/**
 * BloodLife - My Accepted Requests Map
 * Displays donor and hospital locations on interactive map
 */

// Initialize map
let acceptedMap = null;
let markers = {};

// Get user location
let userLocation = null;

// Store request data - loaded from JSON script tag
let requestData = [];

// Load request data from JSON script tag
function loadRequestData() {
    const dataScript = document.getElementById('accepted-requests-data');
    if (dataScript) {
        try {
            requestData = JSON.parse(dataScript.textContent);
        } catch (error) {
            console.error('Error parsing request data:', error);
            requestData = [];
        }
    }
}

function initMap() {
    // Create map centered on India
    acceptedMap = L.map('accepted-requests-map').setView([20.5937, 78.9629], 5);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(acceptedMap);
    
    // Get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Add donor marker (user)
                const donorIcon = L.divIcon({
                    className: 'custom-donor-marker',
                    html: '<i class="bi bi-person-fill" style="color: white; font-size: 20px;"></i>',
                    iconSize: [40, 40],
                    iconAnchor: [20, 20]
                });
                
                L.marker([userLocation.lat, userLocation.lng], { icon: donorIcon })
                    .addTo(acceptedMap)
                    .bindPopup('<b>Your Location</b><br>Donor');
                    
                addAllRequestsToMap();
            },
            function(error) {
                console.warn('Could not get your location:', error);
                addAllRequestsToMap();
            }
        );
    } else {
        addAllRequestsToMap();
    }
}

function addAllRequestsToMap() {
    const bounds = [];
    
    requestData.forEach(function(req) {
        if (req.latitude && req.longitude) {
            // Create custom icon for hospital/requestor
            const requestorIcon = L.divIcon({
                className: 'custom-requestor-marker',
                html: '<i class="bi bi-hospital" style="color: white; font-size: 18px;"></i>',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            });
            
            // Add marker
            const marker = L.marker([req.latitude, req.longitude], { icon: requestorIcon })
                .addTo(acceptedMap)
                .bindPopup(`
                    <b>${req.hospital_name}</b><br>
                    Patient: ${req.patient_name}<br>
                    Blood Group: ${req.blood_group}<br>
                    Status: ${req.status}<br>
                    Priority: ${req.priority}<br>
                    <a href="/requests/${req.id}/track/" class="btn btn-sm btn-primary mt-2">Track Request</a>
                `);
            
            markers[req.id] = marker;
            bounds.push([req.latitude, req.longitude]);
            
            // Draw line from donor to hospital if user location is available
            if (userLocation) {
                L.polyline(
                    [[userLocation.lat, userLocation.lng], [req.latitude, req.longitude]],
                    {
                        color: '#3b82f6',
                        weight: 2,
                        opacity: 0.6,
                        dashArray: '5, 10'
                    }
                ).addTo(acceptedMap);
            }
        }
    });
    
    // Fit map to show all markers
    if (bounds.length > 0) {
        acceptedMap.fitBounds(bounds, { padding: [50, 50] });
    }
}

function focusOnMap(requestId) {
    if (markers[requestId]) {
        acceptedMap.setView(markers[requestId].getLatLng(), 15);
        markers[requestId].openPopup();
    }
}

// Add event listeners to "View on Map" buttons
function setupMapButtons() {
    const buttons = document.querySelectorAll('.view-on-map-btn');
    buttons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const requestId = parseInt(this.getAttribute('data-request-id'));
            focusOnMap(requestId);
        });
    });
}

// Initialize map on page load
document.addEventListener('DOMContentLoaded', function() {
    loadRequestData();
    initMap();
    setupMapButtons();
});
