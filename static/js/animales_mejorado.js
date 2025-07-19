// JavaScript mejorado para la gestión de animales
document.addEventListener('DOMContentLoaded', function() {
    
    // Elementos del DOM
    const searchInput = document.getElementById('searchInput');
    const breedFilter = document.getElementById('breedFilter');
    const sexFilter = document.getElementById('sexFilter');
    const animalesContainer = document.getElementById('animalesContainer');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const animalCards = document.querySelectorAll('.animal-card-wrapper');
    
    // Función para filtrar animales
    function filterAnimals() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedBreed = breedFilter.value.toLowerCase();
        const selectedSex = sexFilter.value.toLowerCase();
        
        let visibleCount = 0;
        
        animalCards.forEach(card => {
            const nombre = card.dataset.nombre.toLowerCase();
            const arete = card.dataset.arete.toLowerCase();
            const raza = card.dataset.raza.toLowerCase();
            const sexo = card.dataset.sexo.toLowerCase();
            
            // Aplicar filtros
            const matchesSearch = nombre.includes(searchTerm) || 
                                arete.includes(searchTerm) || 
                                raza.includes(searchTerm);
            const matchesBreed = !selectedBreed || raza === selectedBreed;
            const matchesSex = !selectedSex || sexo === selectedSex;
            
            if (matchesSearch && matchesBreed && matchesSex) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Mostrar/ocultar mensaje de no resultados
        if (visibleCount === 0) {
            noResultsMessage.style.display = 'block';
            animalesContainer.style.display = 'none';
        } else {
            noResultsMessage.style.display = 'none';
            animalesContainer.style.display = 'block';
        }
    }
    
    // Event listeners para filtros
    if (searchInput) {
        searchInput.addEventListener('input', filterAnimals);
    }
    
    if (breedFilter) {
        breedFilter.addEventListener('change', filterAnimals);
    }
    
    if (sexFilter) {
        sexFilter.addEventListener('change', filterAnimals);
    }
    
    // Función para eliminar animal
    function eliminarAnimal(animalId) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: "Esta acción no se puede deshacer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                // Realizar la eliminación
                window.location.href = `/eliminar-animal/${animalId}`;
            }
        });
    }
    
    // Event listeners para botones de eliminar
    document.querySelectorAll('.btn-eliminar-animal').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const animalId = this.dataset.id;
            eliminarAnimal(animalId);
        });
    });
    
    // Función para mostrar detalles del animal
    function mostrarDetallesAnimal(animalId) {
        // Aquí puedes implementar la lógica para mostrar detalles
        // Por ejemplo, abrir un modal con información detallada
        console.log('Mostrar detalles del animal:', animalId);
    }
    
    // Event listeners para tarjetas de animales
    document.querySelectorAll('.animal-card').forEach(card => {
        card.addEventListener('click', function(e) {
            // No activar si se hace clic en un botón
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
                return;
            }
            
            const animalId = this.querySelector('.btn-eliminar-animal').dataset.id;
            mostrarDetallesAnimal(animalId);
        });
    });
    
    // Función para generar QR
    function generarQR(animalId) {
        // Implementar generación de QR
        console.log('Generar QR para animal:', animalId);
    }
    
    // Función para exportar datos
    function exportarDatos() {
        // Implementar exportación de datos
        console.log('Exportar datos de animales');
    }
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Función para actualizar estadísticas
    function actualizarEstadisticas() {
        const totalAnimales = animalCards.length;
        const hembras = Array.from(animalCards).filter(card => 
            card.dataset.sexo === 'Hembra').length;
        const machos = Array.from(animalCards).filter(card => 
            card.dataset.sexo === 'Macho').length;
        
        // Actualizar contadores en tiempo real
        const totalElement = document.querySelector('.stat-card h3');
        if (totalElement) {
            totalElement.textContent = totalAnimales;
        }
        
        // Aquí puedes actualizar otros contadores si es necesario
        console.log(`Total: ${totalAnimales}, Hembras: ${hembras}, Machos: ${machos}`);
    }
    
    // Llamar a la función de estadísticas al cargar
    actualizarEstadisticas();
    
    // Función para ordenar animales
    function ordenarAnimales(criterio) {
        const container = document.getElementById('animalesContainer');
        const cards = Array.from(container.children);
        
        cards.sort((a, b) => {
            switch(criterio) {
                case 'nombre':
                    return a.dataset.nombre.localeCompare(b.dataset.nombre);
                case 'arete':
                    return a.dataset.arete.localeCompare(b.dataset.arete);
                case 'raza':
                    return a.dataset.raza.localeCompare(b.dataset.raza);
                case 'sexo':
                    return a.dataset.sexo.localeCompare(b.dataset.sexo);
                default:
                    return 0;
            }
        });
        
        // Reinsertar las tarjetas ordenadas
        cards.forEach(card => container.appendChild(card));
    }
    
    // Función para limpiar filtros
    function limpiarFiltros() {
        if (searchInput) searchInput.value = '';
        if (breedFilter) breedFilter.value = '';
        if (sexFilter) sexFilter.value = '';
        filterAnimals();
    }
    
    // Agregar botón de limpiar filtros si no existe
    const filtersContainer = document.querySelector('.animal-filters-advanced');
    if (filtersContainer && !document.querySelector('.btn-limpiar-filtros')) {
        const limpiarBtn = document.createElement('button');
        limpiarBtn.className = 'btn btn-outline-secondary btn-limpiar-filtros';
        limpiarBtn.innerHTML = '<i class="fas fa-times"></i> Limpiar';
        limpiarBtn.addEventListener('click', limpiarFiltros);
        filtersContainer.appendChild(limpiarBtn);
    }
    
    // Función para mostrar mensajes de éxito/error
    function mostrarMensaje(tipo, mensaje) {
        Swal.fire({
            icon: tipo,
            title: mensaje,
            timer: 3000,
            showConfirmButton: false
        });
    }
    
    // Verificar si hay mensajes flash y mostrarlos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const message = alert.textContent.trim();
        const type = alert.classList.contains('alert-success') ? 'success' : 
                    alert.classList.contains('alert-danger') ? 'error' : 'info';
        
        if (message) {
            mostrarMensaje(type, message);
        }
    });
    
    // Función para validar formularios
    function validarFormularioAnimal(form) {
        const nombre = form.querySelector('input[name="nombre"]').value.trim();
        const numeroArete = form.querySelector('input[name="numero_arete"]').value.trim();
        const raza = form.querySelector('select[name="raza"]').value;
        const sexo = form.querySelector('select[name="sexo"]').value;
        
        if (!nombre || nombre.length < 2) {
            mostrarMensaje('error', 'El nombre debe tener al menos 2 caracteres');
            return false;
        }
        
        if (!numeroArete) {
            mostrarMensaje('error', 'El número de arete es obligatorio');
            return false;
        }
        
        if (!raza) {
            mostrarMensaje('error', 'Debe seleccionar una raza');
            return false;
        }
        
        if (!sexo) {
            mostrarMensaje('error', 'Debe seleccionar el sexo');
            return false;
        }
        
        return true;
    }
    
    // Event listener para formularios de animales
    document.querySelectorAll('form').forEach(form => {
        if (form.action.includes('registrar-animal') || form.action.includes('editar-animal')) {
            form.addEventListener('submit', function(e) {
                if (!validarFormularioAnimal(this)) {
                    e.preventDefault();
                }
            });
        }
    });
    
    console.log('JavaScript de animales cargado correctamente');
}); 