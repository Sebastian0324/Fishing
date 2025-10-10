// --- Login toggles (unchanged) ---
let login = document.getElementById("Login");
document.getElementById("Login_btn")?.addEventListener("click", function () {
  login.style.display = "block";
});
document.getElementById("Close_Login")?.addEventListener("click", function () {
  document.getElementById("Login").style.display = "None";
});

// --- Sign in/up toggle (unchanged) ---
let Sign = document.getElementById("SignIn/Up");
let SignIn = document.getElementById("SignIn");
let SignUp = document.getElementById("SignUp");
document.getElementById("SignIn/Up")?.addEventListener("click", function () {
  SignIn.classList.toggle("hidden");
  SignUp.classList.toggle("hidden");
  Sign.classList.toggle("btn-dark");
  Sign.classList.toggle("btn-secondary");
});

// ===== Upload Page =====
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("uploadForm");
  if (!form) return;

  const uploadControls = document.getElementById("uploadControls");
  const dropBox = document.getElementById("dropBox");
  const submitBtn = document.getElementById("submitButton");
  const analysis = document.getElementById("analysis");
  const resultEl = document.getElementById("result");

  const showLoading = () => {
    if (uploadControls) uploadControls.style.display = "none";
    if (dropBox) dropBox.style.display = "none";
    if (submitBtn) submitBtn.style.display = "none";
    if (analysis) analysis.style.display = "block";
    if (resultEl) resultEl.innerHTML = ""; // clear
  };

  const showControls = () => {
    if (uploadControls) uploadControls.style.display = "";
    if (dropBox) dropBox.style.display = "";
    if (submitBtn) submitBtn.style.display = "";
    if (analysis) analysis.style.display = "none";
  };

  form.addEventListener("submit", async function (e) {
    e.preventDefault(); // IMPORTANT: prevent default navigation

    // Basic client validation
    const file = dropBox?.files?.[0];
    if (!file) {
      alert("Please choose a .eml file first");
      return;
    }

    showLoading();

    // Build form data
    const fd = new FormData(form);
    // If you have a logged-in user_id in JS, append it; otherwise omit and backend will use 'anonymous'
    // fd.append("user_id", window.CURRENT_USER_ID || "");

    try {
      const res = await fetch("/upload", { method: "POST", body: fd });
      // Handle non-200s
      let data;
      try {
        data = await res.json();
      } catch {
        throw new Error("Server returned a non-JSON response.");
      }

      if (!res.ok || !data.ok) {
        const msg = (data && data.error) ? data.error : `Upload failed (HTTP ${res.status})`;
        resultEl.innerHTML = `<div class="alert alert-danger" role="alert">${msg}</div>`;
        showControls();
        return;
      }

      // Success UI
      const lines = [
        `<div class="alert alert-success" role="alert"><strong>Uploaded!</strong></div>`,
        `<div class="content-section">`,
        `<p><b>Email ID:</b> ${data.email_id}</p>`,
        data.sha256 ? `<p><b>SHA256:</b> <code>${data.sha256}</code></p>` : ``,
        data.uploader_user_id ? `<p><b>Uploader User_ID:</b> ${data.uploader_user_id}</p>` : ``,
        `</div>`
      ].join("");

      resultEl.innerHTML = lines;
      // Stay on the result; you can keep controls hidden or show an "Upload another" button:
      const againBtn = document.createElement("button");
      againBtn.textContent = "Upload another";
      againBtn.className = "btn btn-secondary";
      againBtn.style.marginTop = "0.5rem";
      againBtn.onclick = () => {
        form.reset();
        showControls();
        resultEl.innerHTML = "";
      };
      resultEl.appendChild(againBtn);

    } catch (err) {
      resultEl.innerHTML = `<div class="alert alert-danger" role="alert">${err.message || err}</div>`;
      showControls();
    }
  });
});

// ===== Account / Forum code (unchanged below this line) =====

// Account Page Toggle
let showEmailsBtn = document.getElementById("showEmailsBtn");
let showSettingsBtn = document.getElementById("showSettingsBtn");
let emailsSection = document.getElementById("emailsSection");
let settingsSection = document.getElementById("settingsSection");

if (showEmailsBtn && showSettingsBtn) {
  showEmailsBtn.addEventListener("click", function () {
    emailsSection.style.display = "block";
    settingsSection.style.display = "none";
    showEmailsBtn.classList.add("active");
    showSettingsBtn.classList.remove("active");
  });

  showSettingsBtn.addEventListener("click", function () {
    emailsSection.style.display = "none";
    settingsSection.style.display = "block";
    showSettingsBtn.classList.add("active");
    showEmailsBtn.classList.remove("active");
  });
}

// Forum Page (placeholder data)
const discussions = { /* ... unchanged ... */ };
const topicItems = document.querySelectorAll(".topic-item");
topicItems.forEach((item) => {
  item.addEventListener("click", function () {
    topicItems.forEach((i) => i.classList.remove("active"));
    this.classList.add("active");
    const title = this.querySelector(".discussion-title").textContent;
    const discussion = discussions[title];
    if (discussion) {
      const discussionHTML = `
        <div class="discussion-header">
          <h2 class="discussion-title-large">${title}</h2>
          <p class="topic-meta">Posted by ${discussion.author} • ${discussion.time}</p>
          <div class="discussion-stats">
            <span class="stat-item"> ${discussion.replies} replies</span>
            <span class="stat-item"> ${discussion.likes} likes</span>
          </div>
        </div>
        <div class="discussion-body">${discussion.content}</div>
        <div class="reply-section">
          <h3>Replies</h3>
          <p class="placeholder-text">Discussion replies would appear here...</p>
        </div>`;
      document.getElementById("discussion-content").innerHTML = discussionHTML;
    }
  });
});
