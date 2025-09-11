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

document.getElementById("uploadForm").onsubmit = async (e) => {
  e.preventDefault();

  let formData = new FormData(e.target);
  let response = await fetch("/upload", { method: "POST", body: formData });
  let data = await response.json();
  
  document.getElementById("result").innerHTML =
    `<b>${data.subject}</b><br>From: ${data.from}<br>${data.preview}`;
};
