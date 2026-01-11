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

document.addEventListener('DOMContentLoaded', () => {
  const list = document.getElementById('drafts-list');
  const confirmModal = document.getElementById('confirmModal');
  const confirmModalText = document.getElementById('confirmModalText');
  const confirmModalConfirm = document.getElementById('confirmModalConfirm');
  const confirmModalCancel = document.getElementById('confirmModalCancel');

  function openConfirm(message){
    return new Promise((resolve) => {
      if(!confirmModal) return resolve(false);
      confirmModalText.textContent = message;
      confirmModal.style.display = 'flex';
      confirmModal.setAttribute('aria-hidden','false');

      function onConfirm(){
        cleanup();
        resolve(true);
      }
      function onCancel(){
        cleanup();
        resolve(false);
      }
      function cleanup(){
        confirmModal.style.display = 'none';
        confirmModal.setAttribute('aria-hidden','true');
        confirmModalConfirm.removeEventListener('click', onConfirm);
        confirmModalCancel.removeEventListener('click', onCancel);
      }

      confirmModalConfirm.addEventListener('click', onConfirm);
      confirmModalCancel.addEventListener('click', onCancel);
    });
  }

  if (!list) return;

  list.addEventListener('click', async (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;
    const postEl = btn.closest('[data-post-id]');
    const postId = postEl.getAttribute('data-post-id');
    const contentEl = postEl.querySelector('.draft-content');
    const statusEl = postEl.querySelector('.draft-status');
    const action = btn.getAttribute('data-action');

    if (action === 'delete') {
      const ok = await openConfirm('Delete this draft?');
      if (!ok) return;
      const url = `/` + `post/${postId}/delete/`;
      try {
        const r = await postAction(url, {});
        if (r.status === 'ok') {
          postEl.remove();
          showToast('Draft deleted');
        } else {
          showStatus(statusEl, r.message || 'Error deleting', false);
        }
      } catch (err) {
        showStatus(statusEl, 'Network error', false);
      }
      return;
    }

    // save or publish
    const url = `/` + `draft/${postId}/action/`;
    const data = { content: contentEl.value, action: action };
    try {
      if (action === 'publish') {
        const ok = await openConfirm('Publish this draft now?');
        if (!ok) return;
      }

      const r = await postAction(url, data);
      if (r.status === 'ok') {
        showStatus(statusEl, r.message || (action === 'publish' ? 'Published' : 'Saved'));
        showToast(r.message || (action === 'publish' ? 'Published' : 'Saved'));
        if (action === 'publish') {
          // remove published draft from list
          postEl.remove();
        }
      } else {
        showStatus(statusEl, r.message || 'Error', false);
      }
    } catch (err) {
      showStatus(statusEl, 'Network error', false);
    }
  });
});
