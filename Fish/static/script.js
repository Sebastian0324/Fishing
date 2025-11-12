
// -------========-------    Sign Up    -------========-------

let login = document.getElementById("Login");
let loginBtn = document.getElementById("Login_btn");
let closeLogin = document.getElementById("Close_Login");

if(document.getElementById("Login_btn")) {
  document.getElementById("Login_btn").addEventListener("click", function() {
    login.style.display = "block";
  });

} else {
  document.getElementById("Logout_btn").addEventListener("click", async function(e) {
    e.preventDefault();
    await fetch("/logout");

    window.open(window.location.href, "_self");
  });
}

document.getElementById("Close_Login").children[1].addEventListener("click", function() {
  document.getElementById("Login").style.display = "None";
});

// --- Sign in/up toggle (unchanged) ---
let Sign = document.getElementById("SignIn/Up");
let SignIn = document.getElementById("SignIn");
let SignUp = document.getElementById("SignUp");

if (Sign && SignIn && SignUp) {
  Sign.addEventListener("click", function() {
    SignIn.classList.toggle("hidden");
    SignUp.classList.toggle("hidden");
    Sign.classList.toggle("btn-dark");
    Sign.classList.toggle("btn-secondary");
});

SignUp.onsubmit = async (e) => {
  e.preventDefault();

  let SignUpForm = new FormData(e.target);
  let SignUpResponse = await fetch("/Signup", { method: "POST", body: SignUpForm });
  let SignUpData = await SignUpResponse.json();

  window.open(window.location.href, "_self");
};
SignIn.onsubmit = async (e) => {
  e.preventDefault();

  let SignInForm = new FormData(e.target);
  let SignInResponse = await fetch("/login", { method: "POST", body: SignInForm });
  let SignInData = await SignInResponse.json();

  window.open(window.location.href, "_self");
};

// -------========-------    Upload Page    -------========-------  
let UpForm = document.getElementById("uploadForm");
let analysis = document.getElementById("analysis");
let submitError = document.getElementById("SubmitError");
let selectedFilesBox = document.getElementById("selectedFiles");

// Maximum file size (1 MB = 1 * 1024 * 1024 bytes)
const MAX_FILE_SIZE = 1 * 1024 * 1024; // 1 MB
const MAX_FILES = 5;

if (UpForm != null) {
  // Show selected file names under the input
  const fileInput = document.getElementById("dropBox");
  if (fileInput) {
    fileInput.addEventListener("change", function () {
      if (!selectedFilesBox) return;
      const files = Array.from(fileInput.files || []);
      if (files.length === 0) {
        selectedFilesBox.innerHTML = "";
        return;
      }
      const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
        else return (bytes / 1048576).toFixed(2) + ' MB';
      };
      
      // Create a DataTransfer to manage files
      const dataTransfer = new DataTransfer();
      files.forEach(f => dataTransfer.items.add(f));
      
      const prevComments = fileInput._preservedComments ?? Array.from(selectedFilesBox.querySelectorAll('.comment-input')).map(t => t.value || '');
      if (fileInput._preservedComments) delete fileInput._preservedComments;
      const items = files.map((f, idx) => {
        const fileNumber = idx + 1;
        const isTooLarge = f.size > MAX_FILE_SIZE;
        const isEmlext = f.name.toLowerCase().endsWith('.eml');
        const errBadge = isTooLarge ? `<span class="badge bg-danger ms-2">Too large</span>` : (!isEmlext ? `<span class="badge bg-warning text-dark ms-2">Invalid type</span>` : '');
        const collapseId = `commentCollapse-${Date.now()}-${idx}`;
        const hasPrev = (prevComments[idx] || '').length > 0;

        return `
        <li class="list-group-item p-2 mb-3 file-item" data-index="${idx}">
          <div class="d-flex">
        <div class="me-3 d-flex align-items-center" style="width:48px;">
          <i class="bi bi-file-earmark-earmark-fill text-primary" style="font-size:1.5rem;"></i>
        </div>

        <div class="flex-grow-1">
          <div class="d-flex justify-content-between align-items-start">
            <div style="min-width:0;">
          <div class="d-flex align-items-center">
            <span class="badge bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center me-2" style="width:34px; height:34px; font-weight:300; font-size:0.95rem;">${fileNumber}</span>
            <div class="fw-semibold text-truncate" title="${f.name}"  >${f.name}</div>
            ${errBadge}
          </div>
          <div class="small text-muted mt-1">${formatFileSize(f.size)}</div>
            </div>

            <div class="text-end ms-3 d-flex flex-column align-items-end gap-2">
          <div>
            <button type="button" class="btn btn-sm btn-outline-secondary me-1 toggle-comment-btn" data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="${hasPrev}" aria-controls="${collapseId}">Comment</button>
            <button type="button" class="btn btn-sm btn-outline-danger remove-file-btn" data-index="${idx}" title="Remove file">
              <i class="bi bi-x-lg"> X </i>
            </button>
          </div>
          ${isTooLarge ? '<small class="text-danger">File exceeds max size</small>' : ''}
            </div>
          </div>

          <div class="collapse ${hasPrev ? 'show' : ''} mt-2" id="${collapseId}">
            <div class="card card-body p-2">
          <textarea
            name="comments[]"
            data-index="${idx}"
            class="form-control form-control-sm comment-input"
            rows="2"
            maxlength="500"
            placeholder="Add a short comment for this file (optional)"
            style="resize: vertical;"
          >${(prevComments[idx] || '').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</textarea>
          <div class="d-flex justify-content-between mt-1 align-items-center">
            <small class="text-muted">Max 500 characters</small>
            <span class="badge bg-light text-dark char-count" data-index="${idx}">${(prevComments[idx] || '').length}/500</span>
          </div>
            </div>
          </div>
        </div>
          </div>
        </li>`;
      }).join('');

            selectedFilesBox.innerHTML = `
        <div class="alert alert-info p-2 mb-2" role="status">
          Selected ${files.length} file${files.length > 1 ? 's' : ''}
        </div>
        <ul class="list-group list-group-flush">${items}</ul>
            `;

            // Attach listeners: remove buttons
            document.querySelectorAll('.remove-file-btn').forEach(btn => {
        btn.addEventListener('click', function() {
          const indexToRemove = parseInt(this.getAttribute('data-index'));

          // Preserve current comments (so we can restore them after re-render)
          const currentComments = Array.from(selectedFilesBox.querySelectorAll('.comment-input')).map(t => t.value || '');
          const newComments = currentComments.filter((_, i) => i !== indexToRemove);

          // Build new DataTransfer without the removed file
          const newDataTransfer = new DataTransfer();
          Array.from(fileInput.files).forEach((file, idx) => {
            if (idx !== indexToRemove) {
              newDataTransfer.items.add(file);
            }
          });

          // Store preserved comments on the input so the change handler can restore them
          fileInput._preservedComments = newComments;

          fileInput.files = newDataTransfer.files;
          // Trigger change to rebuild list UI
          fileInput.dispatchEvent(new Event('change'));
        });
            });

            // Attach listeners: comment inputs -> update char count live
            selectedFilesBox.querySelectorAll('.comment-input').forEach(inp => {
        const idx = inp.getAttribute('data-index');
        const countEl = selectedFilesBox.querySelector(`.char-count[data-index="${idx}"]`);
        const updateCount = () => {
          if (countEl) countEl.textContent = `${inp.value.length}/500`;
        };
        inp.addEventListener('input', updateCount);
        // initialize
        updateCount();
            });
            });
        }


  UpForm.onsubmit = async (e) => {
    e.preventDefault();

  // -------========-------    ERROR HANDLING BEFORE SUBMIT    -------========-------

    // Clear previous errors
    if (submitError) {
      submitError.innerHTML = '';
    }
    
    // Validate file input
    const fileInput = document.getElementById("dropBox");
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      if (submitError) {
        submitError.innerHTML = '<div class="alert alert-danger" role="alert"><strong>Error:</strong> Please select at least one .eml file</div>';
      }
      return;
    }
    
    // Validate number of files
    if (fileInput.files.length > MAX_FILES) {
      if (submitError) {
        submitError.innerHTML = `<div class="alert alert-danger" role="alert"><strong>Error:</strong> Maximum ${MAX_FILES} files allowed</div>`;
      }
      return;
    }
    
    // Validate file type and size
    for (let i = 0; i < fileInput.files.length; i++) {
      const file = fileInput.files[i];
      
      // Check file extension
      if (!file.name.endsWith('.eml')) {
        if (submitError) {
          submitError.innerHTML = '<div class="alert alert-danger" role="alert"><strong>Error:</strong> Only .eml files are allowed</div>';
        }
        return;
      }
      
      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const maxSizeMB = (MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
        if (submitError) {
          submitError.innerHTML = `<div class="alert alert-danger" role="alert"><strong>Error:</strong> File "${file.name}" is ${fileSizeMB} MB. Maximum file size is ${maxSizeMB} MB</div>`;
        }
        return;
      }
    }
    // -------========-------    END OF ERROR HANDLING BEFORE SUBMIT    -------========-------



    // Show analysis section
    toggleAnalysis();
    
    // Show loading spinner
    const loadingSpinner = document.getElementById("loadingSpinner");
    const downloadSection = document.getElementById("downloadSection");
    if (loadingSpinner) loadingSpinner.style.display = "block";
    if (downloadSection) downloadSection.classList.add("hidden");

    let formData = new FormData(e.target);
    let response = await fetch("/upload", { method: "POST", body: formData });
    let data = await response.json();
    
    // Hide loading spinner after response
    setTimeout(() => {
      if (loadingSpinner) loadingSpinner.style.display = "none";
    }, 500);
    
    // Handle error response
    if (data.error) {
      document.getElementById("result").innerHTML = 
        `<div class="alert alert-danger" role="alert"><strong>Error:</strong> ${data.error}</div>`;
      return;
    }
    
    // Handle success response
    if (data.success && data.data) {
      document.getElementById("result").innerHTML = `
        <div class="alert alert-success" role="alert">
          <h5>✓ Email Analysis Complete - ID: ${data.email_id}</h5>
        </div>
      `;
      
      // Show download button after successful analysis
      if (downloadSection) downloadSection.classList.remove("hidden");
      
      // Call LLM API after displaying email analysis
      callLLMAPI(bodyText);
    }
  };
}

function toggleAnalysis() {
  UpForm.classList.toggle("hidden");
  analysis.classList.toggle("hidden");
  
  // Reset analysis section when going back
  if (UpForm.classList.contains("hidden")) {
    // Going to analysis view - do nothing special
  } else {
    // Going back to upload form - reset everything
    const loadingSpinner = document.getElementById("loadingSpinner");
    const downloadSection = document.getElementById("downloadSection");
    const resultDiv = document.getElementById("result");
    
    if (loadingSpinner) loadingSpinner.style.display = "none";
    if (downloadSection) downloadSection.classList.add("hidden");
    if (resultDiv) resultDiv.innerHTML = "";
  }
}

document.getElementById("ToUpload").addEventListener("click", toggleAnalysis);

// -------========-------    End of Upload Page    -------========-------

// -------========-------    Account Page Toggle    -------========-------
document.addEventListener("DOMContentLoaded", function() {
  let showEmailsBtn = document.getElementById("showEmailsBtn");
  let showSettingsBtn = document.getElementById("showSettingsBtn");
  let emailsSection = document.getElementById("emailsSection");
  let settingsSection = document.getElementById("settingsSection");

  if (showEmailsBtn != null && showSettingsBtn != null) {
    showEmailsBtn.addEventListener("click", function() {
      emailsSection.style.display = "block";
      settingsSection.style.display = "none";
      showEmailsBtn.classList.add("active");
      showSettingsBtn.classList.remove("active");
    });

    showSettingsBtn.addEventListener("click", function() {
      emailsSection.style.display = "none";
      settingsSection.style.display = "block";
      showSettingsBtn.classList.add("active");
      showEmailsBtn.classList.remove("active");
    });
  }
});

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
}
