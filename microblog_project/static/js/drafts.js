// AJAX handlers for drafts page

function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';').map(c => c.trim());
  for (const c of cookies) {
    if (c.startsWith(name + '=')) return decodeURIComponent(c.split('=')[1]);
  }
  return '';
}

async function postAction(url, data) {
  const csrftoken = getCSRFToken();
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      'X-CSRFToken': csrftoken,
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: new URLSearchParams(data)
  });
  return resp.json();
}

function showStatus(container, msg, ok=true) {
  container.textContent = msg;
  container.style.color = ok ? 'green' : 'crimson';
  setTimeout(() => container.textContent = '', 3000);
}

function showToast(message) {
  const root = document.getElementById('toast-container');
  if (!root) return;
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = `<div class="toast-msg">${message}</div>`;
  root.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateY(6px)';
    setTimeout(() => t.remove(), 320);
  }, 3000);
}

// Simple CSRF helper
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
  const csrftoken = getCookie('csrftoken');

  function postForm(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
      },
      body: new URLSearchParams(data)
    }).then(res => {
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    });
  }

  document.querySelectorAll('.draft-card').forEach(card => {
    const textarea = card.querySelector('.draft-content');
    const statusEl = card.querySelector('.draft-status');
    const actionUrl = card.dataset.actionUrl;
    const deleteUrl = card.dataset.deleteUrl;

    function showStatus(msg, timeout = 2500) {
      statusEl.textContent = msg;
      if (timeout) setTimeout(() => { if (statusEl.textContent === msg) statusEl.textContent = ''; }, timeout);
    }

    function saveDraft() {
      const content = textarea.value.trim();
      if (content === '') { showStatus('Content cannot be empty', 3000); return Promise.reject(new Error('empty')); }
      showStatus('Saving...');
      return postForm(actionUrl, { content, action: 'save' }).then(json => showStatus(json.message || 'Saved')).catch(() => showStatus('Error saving', 3000));
    }

    function publishDraft() {
      const content = textarea.value.trim();
      if (content === '') { showStatus('Content cannot be empty', 3000); return Promise.reject(new Error('empty')); }
      showStatus('Publishing...');
      return postForm(actionUrl, { content, action: 'publish' }).then(json => { showStatus(json.message || 'Published'); card.remove(); }).catch(() => showStatus('Error publishing', 3000));
    }

    function deleteDraft() {
      if (!confirm('Delete this draft?')) return;
      showStatus('Deleting...');
      postForm(deleteUrl, {}).then(json => { showStatus(json.message || 'Deleted', 1200); card.remove(); }).catch(() => showStatus('Error deleting', 3000));
    }

    card.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-action]');
      if (!btn) return;
      const action = btn.dataset.action;
      if (action === 'save') saveDraft();
      else if (action === 'publish') publishDraft();
      else if (action === 'delete') deleteDraft();
    });

    textarea.addEventListener('keydown', (e) => {
      const isCmd = e.ctrlKey || e.metaKey;
      if (isCmd && e.key.toLowerCase() === 's') { e.preventDefault(); saveDraft(); }
      else if (isCmd && e.key === 'Enter') { e.preventDefault(); publishDraft(); }
    });

    let blurTimer = null;
    textarea.addEventListener('blur', () => {
      clearTimeout(blurTimer);
      blurTimer = setTimeout(() => { if (textarea.value.trim() !== '') saveDraft(); }, 300);
    });
  });
});
