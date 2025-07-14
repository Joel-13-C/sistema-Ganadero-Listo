document.addEventListener('DOMContentLoaded', function() {
    // Ejemplo de función para actualizar datos dinámicamente
    function updateDashboardData() {
        // Aquí podrías hacer una llamada AJAX para obtener datos actualizados
        console.log('Actualizando datos del dashboard');
    }

    // Actualizar datos cada 5 minutos
    setInterval(updateDashboardData, 5 * 60 * 1000);

    // Menú lateral interactivo
    const sidebarLinks = document.querySelectorAll('.sidebar nav ul li a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            sidebarLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
});
