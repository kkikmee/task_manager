document.addEventListener('DOMContentLoaded', function () {
    // Лайки
    const likeButtons = document.querySelectorAll('.like-button');
    const popup = document.getElementById('register-popup');

    likeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const isAuthenticated = button.dataset.isAuthenticated === 'true';
            const objectId = button.dataset.objectId;
            const modelName = button.dataset.modelName;

            if (!isAuthenticated) {
                popup.style.display = 'block';
                setTimeout(() => {
                    popup.style.display = 'none';
                }, 3000);
                return;
            }

            
            fetch('/interactions/like/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ object_id: objectId, model_name: modelName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.liked) {
                    button.textContent = '❤️'; 
                } else {
                    button.textContent = '🤍'; 
                }

                const likeCountElement = document.querySelector(`#total-likes-${objectId}`);
                if (likeCountElement) {
                    likeCountElement.textContent = data.total_likes;
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Загрузка комментариев
    const loadCommentsButtons = document.querySelectorAll('.load-comments-btn');
    
    loadCommentsButtons.forEach(button => {
        button.addEventListener('click', function () {
            const postId = button.dataset.postId;
            
            fetch(`/comments/${postId}/`)
                .then(response => response.json())
                .then(data => {
                    const commentsList = document.querySelector(`#comments-list-${postId}`);
                    commentsList.innerHTML = ''; // Очистить существующие комментарии
                    
                    data.comments.forEach(comment => {
                        const commentItem = document.createElement('li');
                        commentItem.innerHTML = `
                            <p><strong>${comment.username}</strong>: ${comment.text}</p>
                            <small>Добавлено: ${comment.created_at}</small>
                        `;
                        commentsList.appendChild(commentItem);
                    });
                })
                .catch(error => console.error('Error loading comments:', error));
        });
    });

    // Добавление комментария
    const commentForms = document.querySelectorAll('#comment-form');
    commentForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const postId = form.dataset.objectId;
            const text = form.querySelector('#comment-text').value;

            fetch(`/interactions/comment/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ object_id: postId, model_name: 'post', text: text })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const commentsList = document.querySelector(`#comments-list-${postId}`);
                    const newComment = document.createElement('a');
                    newComment.classList.add('d-flex', 'gap-2', 'comment');
                    newComment.href = `/user/profile/${data.comment.username}/`;
                    newComment.innerHTML = `
                            <img src="${data.comment.avatar_url}" class="avatar">
                            <p><strong>${data.comment.username}</strong>: ${data.comment.text}</p>
                            <small>Добавлено: ${data.comment.created }</small>
                    `;
                    commentsList.appendChild(newComment);
                    form.reset();
                }
            })
            .catch(error => console.error('Error submitting comment:', error));
        });
    });
    const images = document.querySelectorAll('.thumbnail'); // Класс для изображений, которые кликабельны
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const closeModal = document.querySelector('.close');

    images.forEach(image => {
        image.addEventListener('click', function () {
            modal.style.display = 'flex';
            modalImg.src = this.src; // Устанавливаем изображение в модальное окно
        });
    });

    // Закрытие модального окна
    closeModal.addEventListener('click', function () {
        modal.style.display = 'none';
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' || event.key === 'Esc') { // Проверка нажатия клавиши Esc
            modal.style.display = 'none';
        }
    });

    // Закрытие окна при клике вне области изображения
    modal.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});