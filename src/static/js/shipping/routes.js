var map;
var directionsService;
var currentRoute;
var directionsRenderers = [];

function initMap() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var currentLat = position.coords.latitude;
            var currentLng = position.coords.longitude;

            map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: currentLat, lng: currentLng },
                zoom: 14
            });

            directionsService = new google.maps.DirectionsService();

            var locationForm = document.getElementById('locationForm');
            locationForm.addEventListener('submit', function (event) {
                event.preventDefault();
                calculateAndDisplayRoute();
            });
        }, function () {
            window.alert('No se pudo obtener la ubicación actual.');
        });
    } else {
        window.alert('Tu navegador no admite la geolocalización.');
    }
}

function calculateAndDisplayRoute() {
    var startLocation = document.getElementById('startLocation').value;
    var endLocation = document.getElementById('endLocation').value;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var currentLat = position.coords.latitude;
            var currentLng = position.coords.longitude;

            var request = {
                origin: startLocation,
                destination: endLocation,
                travelMode: 'DRIVING',
                provideRouteAlternatives: true
            };

            directionsService.route(request, function (response, status) {
                if (status === 'OK') {
                    clearDirections(); // Limpia rutas anteriores

                    // Ordenar las rutas por distancia
                    response.routes.sort(function (a, b) {
                        return getRouteDistance(a) - getRouteDistance(b);
                    });

                    // Nombres y colores para las rutas
                    var routeInfo = [
                        { name: 'Ruta 1 (Azul)', color: 'blue' },
                        { name: 'Ruta 2 (Verde)', color: 'green' }
                    ];

                    // Mostrar las rutas con nombres y colores distintos
                    for (var i = 0; i < Math.min(2, response.routes.length); i++) {
                        var route = response.routes[i];
                        var routeName = routeInfo[i].name;
                        var routeColor = routeInfo[i].color;

                        // Mostrar la distancia de la ruta
                        var distanceKm = getRouteDistance(route) / 1000;
                        var distanceMessage = `Distancia de ${routeName}: ${distanceKm.toFixed(2)} km`;
                        document.getElementById('distanceMessage').innerText += distanceMessage + '\n';

                        // Renderizar la ruta en el mapa con el color correspondiente
                        var renderer = new google.maps.DirectionsRenderer({
                            map: map,
                            directions: response,
                            routeIndex: i,
                            polylineOptions: {
                                strokeColor: routeColor
                            }
                        });
                        directionsRenderers.push(renderer);
                    }

                    // Guardar la primera ruta actual para usarla como base al generar una nueva ruta
                    currentRoute = response;
                } else {
                    window.alert('Error al trazar la ruta: ' + status);
                }
            });
        }, function () {
            window.alert('No se pudo obtener la ubicación actual.');
        });
    } else {
        window.alert('Tu navegador no admite la geolocalización.');
    }
}

function getRouteDistance(route) {
    var distance = 0;
    for (var i = 0; i < route.legs.length; i++) {
        distance += route.legs[i].distance.value;
    }
    return distance;
}

function clearDirections() {
    for (var i = 0; i < directionsRenderers.length; i++) {
        directionsRenderers[i].setMap(null);
    }
    directionsRenderers = [];
    document.getElementById('distanceMessage').innerText = ''; // Limpia el mensaje de distancia
}
