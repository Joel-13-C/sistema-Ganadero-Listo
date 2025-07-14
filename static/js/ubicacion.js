document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando script de ubicación...');
    
    const provinciaSelect = document.getElementById('provincia_id');
    const cantonSelect = document.getElementById('canton_id');
    const parroquiaSelect = document.getElementById('parroquia_id');

    console.log('Elementos encontrados:', {
        provincia: provinciaSelect,
        canton: cantonSelect,
        parroquia: parroquiaSelect
    });

    // Función para cargar cantones
    async function cargarCantones() {
        const provinciaId = provinciaSelect.value;
        console.log('Cargando cantones para provincia:', provinciaId);

        // Limpiar y deshabilitar selects
        cantonSelect.innerHTML = '<option value="">Seleccione un cantón</option>';
        cantonSelect.disabled = true;
        parroquiaSelect.innerHTML = '<option value="">Seleccione una parroquia</option>';
        parroquiaSelect.disabled = true;

        if (!provinciaId) {
            console.log('No se seleccionó provincia');
            return;
        }

        try {
            console.log('Realizando petición a:', `/obtener_cantones/${provinciaId}`);
            const response = await fetch(`/obtener_cantones/${provinciaId}`);
            console.log('Respuesta recibida:', response);

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const cantones = await response.json();
            console.log('Cantones recibidos:', cantones);

            if (Array.isArray(cantones)) {
                cantones.forEach(canton => {
                    const option = document.createElement('option');
                    option.value = canton.id;
                    option.textContent = canton.nombre;
                    cantonSelect.appendChild(option);
                });
                cantonSelect.disabled = false;
                console.log('Cantones cargados exitosamente');
            } else {
                console.error('Formato de respuesta inválido:', cantones);
                throw new Error('Formato de respuesta inválido');
            }
        } catch (error) {
            console.error('Error al cargar cantones:', error);
            alert('Error al cargar los cantones. Por favor, intente nuevamente.');
        }
    }

    // Función para cargar parroquias
    async function cargarParroquias() {
        const cantonId = cantonSelect.value;
        console.log('Cargando parroquias para cantón:', cantonId);

        // Limpiar y deshabilitar select de parroquias
        parroquiaSelect.innerHTML = '<option value="">Seleccione una parroquia</option>';
        parroquiaSelect.disabled = true;

        if (!cantonId) {
            console.log('No se seleccionó cantón');
            return;
        }

        try {
            console.log('Realizando petición a:', `/obtener_parroquias/${cantonId}`);
            const response = await fetch(`/obtener_parroquias/${cantonId}`);
            console.log('Respuesta recibida:', response);

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const parroquias = await response.json();
            console.log('Parroquias recibidas:', parroquias);

            if (Array.isArray(parroquias)) {
                parroquias.forEach(parroquia => {
                    const option = document.createElement('option');
                    option.value = parroquia.id;
                    option.textContent = parroquia.nombre;
                    parroquiaSelect.appendChild(option);
                });
                parroquiaSelect.disabled = false;
                console.log('Parroquias cargadas exitosamente');
            } else {
                console.error('Formato de respuesta inválido:', parroquias);
                throw new Error('Formato de respuesta inválido');
            }
        } catch (error) {
            console.error('Error al cargar parroquias:', error);
            alert('Error al cargar las parroquias. Por favor, intente nuevamente.');
        }
    }

    // Event listeners
    provinciaSelect.addEventListener('change', function(event) {
        console.log('Provincia seleccionada:', {
            value: this.value,
            text: this.options[this.selectedIndex].text
        });
        cargarCantones();
    });

    cantonSelect.addEventListener('change', function(event) {
        console.log('Cantón seleccionado:', {
            value: this.value,
            text: this.options[this.selectedIndex].text
        });
        cargarParroquias();
    });

    console.log('Script de ubicación inicializado correctamente');
});
