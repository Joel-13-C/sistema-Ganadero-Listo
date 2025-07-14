/**
 * Script para la visualización de reportes financieros
 */

// Función para mostrar información de depuración
function mostrarDebug(mensaje) {
    const debugText = document.getElementById('debugText');
    if (debugText) {
        const timestamp = new Date().toLocaleTimeString();
        debugText.textContent += '\n[' + timestamp + '] ' + mensaje;
    }
    console.log(mensaje);
}

// Función para limpiar los mensajes de depuración
function limpiarDebug() {
    const debugText = document.getElementById('debugText');
    if (debugText) {
        debugText.textContent = 'Depuración reiniciada...';
    }
}

// Iniciar depuración
document.addEventListener('DOMContentLoaded', function() {
    mostrarDebug('Iniciando script de reportes financieros');
    
    // Configurar el botón de limpiar debug
    const btnLimpiar = document.getElementById('limpiarDebug');
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', limpiarDebug);
    }
    
    // Inicializar la gráfica
    inicializarGrafica();
});

// Función principal para inicializar la gráfica
function inicializarGrafica() {
    mostrarDebug('Inicializando gráfica');
    
    try {
        // Obtener referencias a los elementos del DOM
        const mensajeNoData = document.getElementById('mensajeNoData');
        if (!mensajeNoData) {
            mostrarDebug('ERROR: No se encontró el elemento mensajeNoData');
            return;
        }
        
        const graficoContainer = document.getElementById('graficoContainer');
        if (!graficoContainer) {
            mostrarDebug('ERROR: No se encontró el elemento graficoContainer');
            return;
        }
        
        const graficoMensual = document.getElementById('graficoMensual');
        if (!graficoMensual) {
            mostrarDebug('ERROR: No se encontró el elemento graficoMensual');
            return;
        }
        
        mostrarDebug('Referencias a elementos DOM obtenidas');
        
        // Obtener los datos pasados desde Flask
        const datosIngresos = window.datosIngresos || [];
        const datosGastos = window.datosGastos || [];
        const etiquetas = window.etiquetas || [];
        const tituloPeriodo = window.tituloPeriodo || '';
        const mesSeleccionado = window.mesSeleccionado || 0;
        
        mostrarDebug('Mes seleccionado: ' + mesSeleccionado);
        mostrarDebug('Título del período: ' + tituloPeriodo);
        mostrarDebug('Etiquetas: ' + JSON.stringify(etiquetas));
        mostrarDebug('Datos de ingresos: ' + JSON.stringify(datosIngresos));
        mostrarDebug('Datos de gastos: ' + JSON.stringify(datosGastos));
        mostrarDebug('Longitud datos ingresos: ' + datosIngresos.length);
        mostrarDebug('Longitud datos gastos: ' + datosGastos.length);
        mostrarDebug('Longitud etiquetas: ' + etiquetas.length);
        
        // Verificar si hay datos para mostrar
        const hayDatosIngresos = datosIngresos && datosIngresos.length > 0 && datosIngresos.some(function(valor) { return valor > 0; });
        const hayDatosGastos = datosGastos && datosGastos.length > 0 && datosGastos.some(function(valor) { return valor > 0; });
        const hayDatos = hayDatosIngresos || hayDatosGastos || (mesSeleccionado > 0);  // Si se seleccionó un mes específico, mostrar la gráfica aunque no haya datos
        
        mostrarDebug('¿Hay datos de ingresos? ' + hayDatosIngresos);
        mostrarDebug('¿Hay datos de gastos? ' + hayDatosGastos);
        mostrarDebug('¿Hay datos en general? ' + hayDatos);
        
        // Configurar visibilidad inicial de los elementos
        mensajeNoData.style.display = 'none';
        graficoContainer.style.display = 'none';
        
        // Verificar dimensiones del contenedor
        mostrarDebug('Dimensiones del contenedor: ' + graficoContainer.offsetWidth + 'x' + graficoContainer.offsetHeight);
        
        if (!hayDatos) {
            // Mostrar mensaje de no hay datos
            mostrarDebug('No hay datos, mostrando mensaje');
            mensajeNoData.style.display = 'block';
            graficoContainer.style.display = 'none';
        } else {
            // Ocultar mensaje y mostrar gráfico
            mostrarDebug('Hay datos, preparando gráfico');
            mensajeNoData.style.display = 'none';
            graficoContainer.style.display = 'block';
            
            // Asegurar que el contenedor sea visible antes de crear el gráfico
            setTimeout(function() {
                mostrarDebug('Dimensiones del contenedor (después de mostrar): ' + 
                           graficoContainer.offsetWidth + 'x' + graficoContainer.offsetHeight);
            
            try {
                // Calcular datos del balance
                const datosBalance = [];
                for (let i = 0; i < datosIngresos.length; i++) {
                    datosBalance.push(datosIngresos[i] - datosGastos[i]);
                }
                
                mostrarDebug('Datos de balance calculados');
                
                // Obtener el contexto del canvas
                const ctx = graficoMensual.getContext('2d');
                if (!ctx) {
                    mostrarDebug('ERROR: No se pudo obtener el contexto 2d del canvas');
                    return;
                }
                mostrarDebug('Contexto del canvas obtenido correctamente');
                
                // Verificar si ya existe un gráfico en este canvas
                if (window.chartInstance) {
                    mostrarDebug('Destruyendo gráfico existente');
                    window.chartInstance.destroy();
                }
                
                mostrarDebug('Creando nueva instancia de Chart.js');
                mostrarDebug('Creando gráfico con ' + etiquetas.length + ' etiquetas');
                window.chartInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: etiquetas,
                        datasets: [
                            {
                                label: 'Ingresos',
                                data: datosIngresos,
                                borderColor: 'rgb(40, 167, 69)',
                                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                tension: 0.4,
                                pointRadius: 4,
                                pointBackgroundColor: 'rgb(40, 167, 69)'
                            },
                            {
                                label: 'Gastos',
                                data: datosGastos,
                                borderColor: 'rgb(220, 53, 69)',
                                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                tension: 0.4,
                                pointRadius: 4,
                                pointBackgroundColor: 'rgb(220, 53, 69)'
                            },
                            {
                                label: 'Balance',
                                data: datosBalance,
                                borderColor: 'rgb(0, 123, 255)',
                                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                fill: false,
                                tension: 0.4,
                                pointRadius: 4,
                                pointBackgroundColor: 'rgb(0, 123, 255)'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Evolución Financiera: ' + tituloPeriodo,
                                font: {
                                    size: 16
                                }
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.y !== null) {
                                            label += new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(context.parsed.y);
                                        }
                                        return label;
                                    }
                                }
                            },
                            legend: {
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value.toLocaleString('es-MX');
                                    }
                                },
                                title: {
                                    display: true,
                                    text: 'Monto ($)'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: mesSeleccionado > 0 ? 'Día' : 'Mes'
                                }
                            }
                        }
                    }
                });
                
                mostrarDebug('Chart.js ha creado la instancia del gráfico');
                mostrarDebug('Gráfico creado correctamente');
            } catch (error) {
                mostrarDebug('Error al crear el gráfico: ' + error.message);
                console.error(error);
            }
            }, 100); // Esperar 100ms para que el DOM se actualice
        }
    } catch (error) {
        mostrarDebug('Error general: ' + error.message);
        console.error(error);
    }
}
