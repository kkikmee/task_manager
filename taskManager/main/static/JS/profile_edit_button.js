document.addEventListener('DOMContentLoaded', function () {
    // Код для редактирования профиля
    const editButton = document.querySelector('#edit-profile-button');
    const editForm = document.querySelector('#edit-profile-form');

    if (editButton && editForm) {
        editButton.addEventListener('click', function () {
            if (editForm.style.display === 'none' || editForm.style.display === '') {
                editForm.style.display = 'block'; 
                editButton.textContent = 'Cancel';
            } else {
                editForm.style.display = 'none';
                editButton.textContent = 'Edit Profile';
            }
        });
    }

    const addButton = document.getElementById('add-more-images');
    const formsetContainer = document.getElementById('image-formset');
    
    if (addButton && formsetContainer) {
        addButton.addEventListener('click', function () {
            const totalFormsInput = document.querySelector('#id_form-TOTAL_FORMS');
            const totalForms = parseInt(totalFormsInput.value);

            const lastForm = formsetContainer.querySelector('.form-row:last-child');
            const newForm = lastForm.cloneNode(true);

            newForm.querySelectorAll('input, label').forEach(function (element) {
                if (element.name) {
                    element.name = element.name.replace(`-${totalForms - 1}-`, `-${totalForms}-`);
                }
                if (element.id) {
                    element.id = element.id.replace(`-${totalForms - 1}-`, `-${totalForms}-`);
                }
                if (element.type === 'file') {
                    element.value = ''; 
                }
            });

            formsetContainer.appendChild(newForm);
            totalFormsInput.value = totalForms + 1;
        });
    }
});