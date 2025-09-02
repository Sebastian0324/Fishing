document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-test');
  const out = document.getElementById('result');

  btn.addEventListener('click', async () => {
    try {
      const res = await fetch('/test', { method: 'POST' });
      const text = await res.text();
      out.textContent = text; // show response
    } catch (e) {
      console.error(e);
      out.textContent = 'Error';
    }
  });
});
