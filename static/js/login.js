document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const username = loginForm.querySelector('input[name="username"]');
            const password = loginForm.querySelector('input[name="password"]');
            
            // Validación de longitud de usuario
            if (username.value.length < 3) {
                event.preventDefault();
                alert('El nombre de usuario debe tener al menos 3 caracteres');
                return;
            }
            
            // Validación de contraseña
            if (password.value.length < 6) {
                event.preventDefault();
                alert('La contraseña debe tener al menos 6 caracteres');
                return;
            }
        });
    }
});
