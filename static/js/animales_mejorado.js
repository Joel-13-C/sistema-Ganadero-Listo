/**
 * Script mejorado para el módulo de animales
 * Agrega funcionalidades visuales y mejora la experiencia de usuario
 */

document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const searchInput = document.getElementById('searchInput');
    const breedFilter = document.getElementById('breedFilter');
    const sexFilter = document.getElementById('sexFilter');
    const animalesContainer = document.getElementById('animalesContainer');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const animalCards = document.querySelectorAll('.animal-card-wrapper');
    
    // Función para filtrar animales
    function filterAnimals() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedBreed = breedFilter.value;
        const selectedSex = sexFilter.value;
        
        let visibleCount = 0;
        
        animalCards.forEach(card => {
            const nombre = card.dataset.nombre.toLowerCase();
            const arete = card.dataset.arete.toLowerCase();
            const raza = card.dataset.raza;
            const sexo = card.dataset.sexo;
            
            // Verificar si cumple con todos los filtros
            const matchesSearch = nombre.includes(searchTerm) || arete.includes(searchTerm) || raza.toLowerCase().includes(searchTerm);
            const matchesBreed = selectedBreed === '' || raza === selectedBreed;
            const matchesSex = selectedSex === '' || sexo === selectedSex;
            
            // Mostrar u ocultar según los filtros
            if (matchesSearch && matchesBreed && matchesSex) {
                card.style.display = 'block';
                // Agregar animación de aparición
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                
                // Aplicar animación con un retraso basado en el índice
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, visibleCount * 50);
                
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Mostrar mensaje de "sin resultados" si no hay coincidencias
        if (visibleCount === 0) {
            noResultsMessage.style.display = 'block';
        } else {
            noResultsMessage.style.display = 'none';
        }
    }
    
    // Agregar eventos para los filtros
    if (searchInput) searchInput.addEventListener('input', filterAnimals);
    if (breedFilter) breedFilter.addEventListener('change', filterAnimals);
    if (sexFilter) sexFilter.addEventListener('change', filterAnimals);
    
    // Función para eliminar un animal
    function setupDeleteButtons() {
        const deleteButtons = document.querySelectorAll('.btn-eliminar-animal');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                const animalId = this.dataset.id;
                
                // Mostrar confirmación con SweetAlert2
                Swal.fire({
                    title: '¿Estás seguro?',
                    text: 'Esta acción no se puede deshacer',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#ef4444',
                    cancelButtonColor: '#64748b',
                    confirmButtonText: 'Sí, eliminar',
                    cancelButtonText: 'Cancelar',
                    background: '#ffffff',
                    customClass: {
                        confirmButton: 'btn btn-danger',
                        cancelButton: 'btn btn-secondary'
                    }
                }).then((result) => {
                    if (result.isConfirmed) {
                        // Redirigir a la ruta de eliminación
                        window.location.href = `/eliminar-animal/${animalId}`;
                    }
                });
            });
        });
    }
    
    // Configurar botones de eliminación
    setupDeleteButtons();
    
    // Agregar vista previa de detalles al hacer clic en la tarjeta
    function setupCardPreviews() {
        const cardBodies = document.querySelectorAll('.animal-card .card-body');
        
        // Crear el popup de detalles si no existe
        if (!document.querySelector('.animal-details-popup')) {
            const popupHTML = `
                <div class="animal-details-popup">
                    <div class="animal-details-content">
                        <i class="fas fa-times close-details"></i>
                        <div class="animal-details-body"></div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', popupHTML);
            
            // Agregar evento para cerrar el popup
            document.querySelector('.close-details').addEventListener('click', function() {
                document.querySelector('.animal-details-popup').classList.remove('active');
            });
            
            // Cerrar al hacer clic fuera del contenido
            document.querySelector('.animal-details-popup').addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.remove('active');
                }
            });
        }
        
        // Agregar evento a cada tarjeta
        cardBodies.forEach(cardBody => {
            const card = cardBody.closest('.animal-card');
            const cardWrapper = card.closest('.animal-card-wrapper');
            
            cardBody.addEventListener('click', function(e) {
                // No activar si se hace clic en los botones
                if (e.target.closest('.animal-actions')) return;
                
                const popup = document.querySelector('.animal-details-popup');
                const popupContent = document.querySelector('.animal-details-body');
                
                // Obtener datos del animal
                const nombre = cardWrapper.dataset.nombre;
                const arete = cardWrapper.dataset.arete;
                const raza = cardWrapper.dataset.raza;
                const sexo = cardWrapper.dataset.sexo;
                const imagen = card.querySelector('.card-img-top').src;
                const condicion = card.querySelector('.card-text').textContent.match(/Condición: ([^\n]+)/)[1].trim();
                
                // Crear contenido HTML para el popup
                const detailsHTML = `
                    <div class="row">
                        <div class="col-md-5">
                            <img src="${imagen}" class="img-fluid rounded" alt="${nombre}">
                        </div>
                        <div class="col-md-7">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h2>${nombre}</h2>
                                <span class="badge ${sexo === 'Macho' ? 'bg-primary' : 'bg-success'} fs-6">${sexo}</span>
                            </div>
                            <div class="animal-details-info">
                                <p><strong>Número de Arete:</strong> ${arete}</p>
                                <p><strong>Raza:</strong> ${raza}</p>
                                <p><strong>Condición:</strong> ${condicion}</p>
                                
                                <div class="mt-4">
                                    <h4>Acciones Rápidas</h4>
                                    <div class="d-flex gap-2 mt-3">
                                        <a href="/editar-animal/${cardWrapper.querySelector('.btn-eliminar-animal').dataset.id}" class="btn btn-primary">
                                            <i class="fas fa-edit me-2"></i>Editar Información
                                        </a>
                                        <button class="btn btn-danger btn-eliminar-animal" data-id="${cardWrapper.querySelector('.btn-eliminar-animal').dataset.id}">
                                            <i class="fas fa-trash me-2"></i>Eliminar
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Actualizar y mostrar el popup
                popupContent.innerHTML = detailsHTML;
                popup.classList.add('active');
                
                // Configurar el botón de eliminar en el popup
                setupDeleteButtons();
            });
        });
    }
    
    // Configurar vista previa de tarjetas
    setupCardPreviews();
    
    // Agregar efectos de carga
    function addLoadingEffects() {
        animalCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    // Aplicar efectos de carga
    addLoadingEffects();
});
