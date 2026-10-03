import { api } from '../api.js';
import { formData, toast } from '../ui.js';

export function init(root) {
  const form = root.querySelector('#register-form');
  const error = root.querySelector('[data-error]');

  form.addEventListener('submit', async event => {
    event.preventDefault();
    error.textContent = '';
    const { password2, ...body } = formData(form);
    if (body.password !== password2) {
      error.textContent = 'Пароли не совпадают';
      return;
    }
    try {
      await api('/auth/register', { method: 'POST', body, auth: false });
      toast('Заявка отправлена. Дождитесь подтверждения администратором.');
      location.hash = '#/login';
    } catch (e) {
      error.textContent = e.message;
    }
  });
  form.elements.full_name.focus();
}
