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


// -------========-------    Front Page    -------========-------
// -------========-------    Upload Page    -------========-------  
let UpForm = document.getElementById("uploadForm");
let analysis = document.getElementById("analysis");
if (UpForm != null) {
  UpForm.onsubmit = async (e) => {
    e.preventDefault();

  toggleAnalysis();

    let formData = new FormData(e.target);
    let response = await fetch("/upload", { method: "POST", body: formData });
    let data = await response.json();
    
    // Handle error response
    if (data.error) {
      document.getElementById("result").innerHTML = 
        `<div class="alert alert-danger" role="alert"><strong>Error:</strong> ${data.error}</div>`;
      return;
    }
    
    // Handle success response with extracted data
    if (data.success && data.data) {
      let urlsList = '';
      if (data.data.urls && data.data.urls.length > 0) {
        urlsList = '<ul class="list-group mt-2">';
        data.data.urls.forEach(url => {
          urlsList += `<li class="list-group-item">${url}</li>`;
        });
        urlsList += '</ul>';
      } else {
        urlsList = '<p class="text-muted">No URLs found</p>';
      }
      
      // Escape HTML for safe display
      const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      };
      
      const bodyText = data.data.body_text || 'No content';
      const bodyLength = data.data.body_length || bodyText.length;
      
      document.getElementById("result").innerHTML = `
        <div class="alert alert-success" role="alert">
          <h5>Email Analysis Complete - ID: ${data.email_id}</h5>
        </div>
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">Email Details</h6>
            <p><strong>From:</strong> ${data.data.sender_email || 'Unknown'}</p>
            <p><strong>Sender IP:</strong> ${data.data.sender_ip || 'Not found'}</p>
            <hr>
            <h6 class="card-subtitle mb-2 text-muted">Full Email Body (${bodyLength} characters)</h6>
            <div style="max-height: 400px; overflow-y: auto; background-color: #000000; color: #ffffff; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: monospace; font-size: 0.9em; border: 1px solid #333333;">
${escapeHtml(bodyText)}
            </div>
            <hr>
            <h6 class="card-subtitle mb-2 text-muted">Extracted URLs (${data.data.urls_count || 0})</h6>
            ${urlsList}
          </div>
        </div>
      `;
    }
  };
}

function toggleAnalysis() {
  UpForm.classList.toggle("hidden");
  analysis.classList.toggle("hidden");
}

document.getElementById("ToUpload").addEventListener("click", toggleAnalysis);

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
