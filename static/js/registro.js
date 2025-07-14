document.addEventListener('DOMContentLoaded', function() {
    const registroForm = document.querySelector('form');
    
    if (registroForm) {
        registroForm.addEventListener('submit', function(event) {
            const username = registroForm.querySelector('input[name="username"]');
            const email = registroForm.querySelector('input[name="email"]');
            const password = registroForm.querySelector('input[name="password"]');
            const confirmPassword = registroForm.querySelector('input[name="confirm_password"]');
            
            // Validación de longitud de usuario
            if (username.value.length < 3) {
                event.preventDefault();
                alert('El nombre de usuario debe tener al menos 3 caracteres');
                return;
            }
            
            // Validación de email
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email.value)) {
                event.preventDefault();
                alert('Por favor, introduce un correo electrónico válido');
                return;
            }
            
            // Validación de contraseña
            if (password.value.length < 6) {
                event.preventDefault();
                alert('La contraseña debe tener al menos 6 caracteres');
                return;
            }
            
            // Validación de coincidencia de contraseñas
            if (password.value !== confirmPassword.value) {
                event.preventDefault();
                alert('Las contraseñas no coinciden');
                return;
            }
        });
    }
});
