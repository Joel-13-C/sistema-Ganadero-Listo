document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const breedFilter = document.getElementById('breedFilter');
    const sexFilter = document.getElementById('sexFilter');
    const animalesContainer = document.getElementById('animalesContainer');
    const noResultsMessage = document.getElementById('noResultsMessage');

    function filtrarAnimales() {
        const searchTerm = searchInput.value.toLowerCase();
        const razaSeleccionada = breedFilter.value;
        const sexoSeleccionado = sexFilter.value;

        const animalCards = animalesContainer.querySelectorAll('.animal-card-wrapper');
        let animalesVisibles = 0;

        animalCards.forEach(card => {
            const nombre = card.dataset.nombre.toLowerCase();
            const arete = card.dataset.arete.toLowerCase();
            const raza = card.dataset.raza.toLowerCase();
            const sexo = card.dataset.sexo;

            const cumpleBusqueda = nombre.includes(searchTerm) || 
                                   arete.includes(searchTerm) || 
                                   raza.includes(searchTerm);
            const cumpleRaza = razaSeleccionada === '' || raza === razaSeleccionada.toLowerCase();
            const cumpleSexo = sexoSeleccionado === '' || sexo === sexoSeleccionado;

            const esVisible = cumpleBusqueda && cumpleRaza && cumpleSexo;
            card.style.display = esVisible ? 'block' : 'none';

            if (esVisible) animalesVisibles++;
        });

        // Mostrar u ocultar mensaje de no resultados
        noResultsMessage.style.display = animalesVisibles === 0 ? 'block' : 'none';
    }

    // Botones de eliminación con SweetAlert
    const botonesEliminar = document.querySelectorAll('.btn-eliminar-animal');
    botonesEliminar.forEach(boton => {
        boton.addEventListener('click', function() {
            const animalId = this.dataset.id;
            
            Swal.fire({
                title: '¿Estás seguro?',
                text: "No podrás revertir esta acción",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = `/eliminar-animal/${animalId}`;
                }
            });
        });
    });

    // Eventos de filtrado
    searchInput.addEventListener('input', filtrarAnimales);
    breedFilter.addEventListener('change', filtrarAnimales);
    sexFilter.addEventListener('change', filtrarAnimales);
});
