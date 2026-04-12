/**
 * Live Donor Tracking System
 * Real-time GPS location streaming and map visualization
 * Similar to Zomato/Swiggy delivery tracking
 */

class LiveDonorTracking {
    constructor(requestId, userId, userRole = 'donor') {
        this.requestId = requestId;
        this.userId = userId;
        this.userRole = userRole; // 'donor' or 'requester'
        this.ws = null;
        this.map = null;
        this.donorMarker = null;
        this.hospitalMarker = null;
        this.routePolyline = null;
        this.watchId = null;
        this.updateInterval = null;
        this.lastLocation = null;
        
        this.init();
    }
    
    init() {
        this.initializeMap();
        this.connectWebSocket();
        
        if (this.userRole === 'donor') {
            this.startLocationTracking();
        } else {
            this.loadDonorLocations();
        }
    }
    
    initializeMap() {
        const mapContainer = document.getElementById('tracking-map');
        if (!mapContainer) return;
        
        // Initialize Leaflet map
        this.map = L.map('tracking-map').setView([20.5937, 78.9629], 5);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        // Load hospital location
        this.loadHospitalLocation();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/request/${this.requestId}/`;
        
        console.log('Connecting to tracking WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ Tracking WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleTrackingUpdate(data);
        };
        
        this.ws.onclose = () => {
            console.log('❌ Tracking WebSocket disconnected');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    startLocationTracking() {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }
        
        // Request permission and start watching
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log('✅ Location permission granted');
                this.startStreaming(position);
            },
            (error) => {
                console.error('Location error:', error);
                alert('Unable to get your location. Please enable location services.');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }
    
    startStreaming(initialPosition) {
        // Send initial location
        this.sendLocationUpdate(initialPosition);
        
        // Watch position changes
        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                this.sendLocationUpdate(position);
            },
            (error) => {
                console.error('Watch position error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
        
        // Also send periodic updates (every 10 seconds)
        this.updateInterval = setInterval(() => {
            navigator.geolocation.getCurrentPosition(
                (position) => this.sendLocationUpdate(position),
                (error) => console.error('Periodic update error:', error)
            );
        }, 10000);
        
        console.log('📍 Location streaming started');
    }
    
    sendLocationUpdate(position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        const accuracy = position.coords.accuracy;
        
        // Don't send if location hasn't changed significantly
        if (this.lastLocation) {
            const distance = this.calculateDistance(
                this.lastLocation.lat,
                this.lastLocation.lng,
                latitude,
                longitude
            );
            
            if (distance < 10) return; // Less than 10 meters, skip update
        }
        
        this.lastLocation = { lat: latitude, lng: longitude };
        
        // Send via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'location_update',
                donor_id: this.userId,
                request_id: this.requestId,
                latitude: latitude,
                longitude: longitude,
                accuracy: accuracy,
                timestamp: new Date().toISOString(),
                speed: position.coords.speed || 0
            }));
        }
        
        // Update marker on donor's map
        this.updateDonorMarker(latitude, longitude);
    }
    
    handleTrackingUpdate(data) {
        console.log('Tracking update:', data);
        
        switch(data.type) {
            case 'donor_location':
                this.updateDonorOnMap(data);
                break;
            
            case 'initial_state':
                this.loadInitialState(data.data);
                break;
            
            case 'status_update':
                this.handleStatusUpdate(data);
                break;
        }
    }
    
    updateDonorOnMap(data) {
        const { donor_id, latitude, longitude } = data;
        
        // If it's my location, update my marker
        if (donor_id === this.userId) {
            this.updateDonorMarker(latitude, longitude);
        } else {
            // Update other donor markers (for requester view)
            this.updateOtherDonorMarker(donor_id, latitude, longitude);
        }
        
        // Calculate ETA if hospital location is known
        if (this.hospitalMarker) {
            const eta = this.calculateETA(latitude, longitude);
            this.updateETADisplay(eta);
        }
    }
    
    updateDonorMarker(latitude, longitude) {
        if (this.donorMarker) {
            this.donorMarker.setLatLng([latitude, longitude]);
        } else {
            this.donorMarker = L.marker([latitude, longitude], {
                icon: L.divIcon({
                    className: 'donor-marker',
                    html: '<div style="background: #10b981; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            }).addTo(this.map);
        }
        
        // Center map on donor
        this.map.setView([latitude, longitude], 16);
        
        // Draw route to hospital
        if (this.hospitalMarker) {
            this.drawRoute([latitude, longitude], this.hospitalMarker.getLatLng());
        }
    }
    
    updateOtherDonorMarker(donorId, latitude, longitude) {
        // For requester: show multiple donors on map
        if (!this.otherDonorMarkers) {
            this.otherDonorMarkers = {};
        }
        
        if (this.otherDonorMarkers[donorId]) {
            this.otherDonorMarkers[donorId].setLatLng([latitude, longitude]);
        } else {
            this.otherDonorMarkers[donorId] = L.marker([latitude, longitude], {
                icon: L.divIcon({
                    className: 'donor-marker',
                    html: '<div style="background: #3b82f6; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                })
            }).addTo(this.map);
        }
    }
    
    async loadHospitalLocation() {
        try {
            const response = await fetch(`/api/requests/${this.requestId}/`);
            const data = await response.json();
            
            if (data.success || data.request) {
                const request = data.request || data;
                const lat = parseFloat(request.latitude);
                const lng = parseFloat(request.longitude);
                
                if (!isNaN(lat) && !isNaN(lng)) {
                    this.hospitalMarker = L.marker([lat, lng], {
                        icon: L.divIcon({
                            className: 'hospital-marker',
                            html: '<div style="background: #ef4444; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">🏥</div>',
                            iconSize: [30, 30],
                            iconAnchor: [15, 15]
                        })
                    }).addTo(this.map);
                    
                    this.hospitalMarker.bindPopup(`<b>${request.hospital_name}</b>`);
                    
                    // Fit map to show both markers if donor location is known
                    if (this.donorMarker) {
                        const group = L.featureGroup([this.donorMarker, this.hospitalMarker]);
                        this.map.fitBounds(group.getBounds(), { padding: [50, 50] });
                    }
                }
            }
        } catch (error) {
            console.error('Error loading hospital location:', error);
        }
    }
    
    drawRoute(donorLatLng, hospitalLatLng) {
        // Remove old route
        if (this.routePolyline) {
            this.map.removeLayer(this.routePolyline);
        }
        
        // Draw straight line (can be enhanced with actual routing API)
        this.routePolyline = L.polyline([donorLatLng, hospitalLatLng], {
            color: '#10b981',
            weight: 4,
            opacity: 0.7,
            dashArray: '10, 10'
        }).addTo(this.map);
    }
    
    calculateETA(currentLat, currentLng) {
        if (!this.hospitalMarker) return null;
        
        const hospitalLatLng = this.hospitalMarker.getLatLng();
        const distance = this.calculateDistance(
            currentLat, currentLng,
            hospitalLatLng.lat, hospitalLatLng.lng
        );
        
        // Assume average speed of 30 km/h in city
        const avgSpeed = 30; // km/h
        const timeHours = distance / avgSpeed;
        const timeMinutes = Math.round(timeHours * 60);
        
        return {
            distance: distance.toFixed(1),
            time: timeMinutes
        };
    }
    
    updateETADisplay(eta) {
        if (!eta) return;
        
        const etaElement = document.getElementById('eta-display');
        if (etaElement) {
            etaElement.textContent = `${eta.time} min (${eta.distance} km)`;
        }
    }
    
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = this.toRad(lat2 - lat1);
        const dLon = this.toRad(lon2 - lon1);
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(this.toRad(lat1)) * Math.cos(this.toRad(lat2)) * 
            Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
    
    toRad(degrees) {
        return degrees * (Math.PI / 180);
    }
    
    async loadDonorLocations() {
        // For requester: load all donor locations
        try {
            const response = await fetch(`/api/requests/${this.requestId}/donors/`);
            const data = await response.json();
            
            if (data.success && data.donors) {
                data.donors.forEach(donor => {
                    if (donor.latitude && donor.longitude) {
                        this.updateOtherDonorMarker(donor.id, donor.latitude, donor.longitude);
                    }
                });
            }
        } catch (error) {
            console.error('Error loading donor locations:', error);
        }
    }
    
    loadInitialState(data) {
        // Load initial request state from WebSocket
        console.log('Initial state loaded:', data);
    }
    
    handleStatusUpdate(data) {
        // Handle status changes (En Route, Arrived, etc.)
        console.log('Status update:', data);
        
        // Show notification
        if (data.message) {
            this.showNotification(data.message);
        }
    }
    
    showNotification(message) {
        // Use existing notification system or browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Blood Donation Update', {
                body: message,
                icon: '/static/icons/icon-192.png'
            });
        }
    }
    
    stopTracking() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
        }
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.ws) {
            this.ws.close();
        }
        
        console.log('🛑 Location tracking stopped');
    }
}

// Initialize tracking when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const trackingContainer = document.getElementById('tracking-container');
    if (trackingContainer) {
        const requestId = trackingContainer.dataset.requestId;
        const userId = trackingContainer.dataset.userId;
        const userRole = trackingContainer.dataset.userRole || 'donor';
        
        if (requestId && userId) {
            window.tracking = new LiveDonorTracking(requestId, userId, userRole);
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.tracking) {
        window.tracking.stopTracking();
    }
});
