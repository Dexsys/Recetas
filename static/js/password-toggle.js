document.addEventListener('DOMContentLoaded', function () {
    var toggles = document.querySelectorAll('.password-toggle[data-target]');

    toggles.forEach(function (toggle) {
        toggle.addEventListener('click', function () {
            var targetId = toggle.getAttribute('data-target');
            var input = document.getElementById(targetId);

            if (!input) {
                return;
            }

            var showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            toggle.setAttribute('aria-pressed', String(!showing));
            toggle.setAttribute('aria-label', showing ? 'Mostrar contraseña' : 'Ocultar contraseña');
            toggle.textContent = showing ? '👁' : '🙈';
        });
    });
});
