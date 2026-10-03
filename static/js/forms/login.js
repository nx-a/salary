import { api, session } from '../api.js';
import { formData } from '../ui.js';

export function init(root) {
  const form = root.querySelector('#login-form');
  const error = root.querySelector('[data-error]');

  form.addEventListener('submit', async event => {
    event.preventDefault();
    error.textContent = '';
    try {
      const { access_token, user } = await api('/auth/login', { method: 'POST', body: formData(form), auth: false });
      session.save(access_token, user);
      location.hash = user.role === 'admin' ? '#/admin/employees' : '#/profile';
    } catch (e) {
      error.textContent = e.message;
    }
  });
  form.elements.login.focus();
}
