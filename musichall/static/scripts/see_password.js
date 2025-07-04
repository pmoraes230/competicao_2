document.addEventListener("DOMContentLoaded", function() {
    const passwordInput = document.getElementById("senha")
    const eye = document.getElementById("eye")

    eye.addEventListener('click', function() {
        if(passwordInput.type == 'password') {
            passwordInput.type = 'text'
            eye.src = '/static/icons/desktop/EyeClose.svg'
        } else {
            passwordInput.type = 'password'
            eye.src = '/static/icons/desktop/eye.svg'
        }
    })
})