// Zaškrtávátko "telefon viditelný" má smysl jen tehdy, když je vyplněné číslo -
// dokud je pole telefonu prázdné, volbu schováme.
(function () {
    function setup() {
        const phoneInput = document.getElementById('id_phone_number');
        const visibleCheckbox = document.getElementById('id_phone_visible');
        if (!phoneInput || !visibleCheckbox) {
            return;
        }

        const wrapper = visibleCheckbox.closest('.mb-3') || visibleCheckbox.parentElement;

        function toggle() {
            wrapper.classList.toggle('d-none', phoneInput.value.trim() === '');
        }

        phoneInput.addEventListener('input', toggle);
        toggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
