(function(){
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) { cookieValue = decodeURIComponent(cookie.substring(name.length + 1)); break; }
            }
        }
        return cookieValue;
    }

    document.addEventListener('click', function(e){
        const btn = e.target.closest('.bookmark-toggle');
        if (!btn) return;
        e.preventDefault();

        const url = btn.getAttribute('data-toggle-url');
        if (!url) return;
        const csrftoken = getCookie('csrftoken');

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin'
        }).then(r => r.json()).then(json => {
            if (!json) return;
            if (json.status !== 'ok') {
                if (json.message) console.warn(json.message);
                return;
            }

            const span = btn.parentElement && btn.parentElement.querySelector('.bookmark-count');
            if (span) span.textContent = json.bookmark_count;

            if (json.bookmarked) {
                btn.classList.add('bookmarked');
                btn.setAttribute('data-bookmarked', '1');
            } else {
                btn.classList.remove('bookmarked');
                btn.setAttribute('data-bookmarked', '0');

                // If we're on the bookmarks page, remove the post element from the list
                try {
                    if (window.location.pathname && window.location.pathname.includes('/bookmarks')) {
                        const postEl = btn.closest('article.post');
                        if (postEl) postEl.remove();

                        // If no posts remain, show the empty state message (matches template)
                        const postsList = document.querySelectorAll('section.posts-list article.post');
                        if (postsList.length === 0) {
                            const container = document.querySelector('section.posts-list');
                            if (container) {
                                const p = document.createElement('p');
                                p.textContent = "You haven't bookmarked any posts yet.";
                                container.appendChild(p);
                            }
                        }
                    }
                } catch (err) {
                    console.warn('Could not remove post element from bookmarks list', err);
                }
            }
        }).catch(err => {
            console.error('Bookmark toggle failed', err);
        });
    });

})();
