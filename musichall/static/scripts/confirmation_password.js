document.getElementById("DomContentLoaded", function() {
    const senhaInput = document.getElementById("senha");
    const confirmacaoInput = document.getElementById("confirmacao_senha");
    const eye = document.getElementById("eye");
    const eyeConfirm = document.getElementById("eye_confirm");

    eye.addEventListener('click', function() {
        if (senhaInput.type === 'password') {
            senhaInput.type = 'text';
            eye.src = '/static/icons/desktop/EyeClose.svg';
        } else {
            senhaInput.type = 'password';
            eye.src = '/static/icons/desktop/eye.svg';
        }
    });

    eyeConfirm.addEventListener('click', function() {
        if (confirmacaoInput.type === 'password') {
            confirmacaoInput.type = 'text';
            eyeConfirm.src = '/static/icons/desktop/EyeClose.svg';
        } else {
            confirmacaoInput.type = 'password';
            eyeConfirm.src = '/static/icons/desktop/eye.svg';
        }
    });
})