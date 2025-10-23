
// -------========-------    Sign Up    -------========-------

let login = document.getElementById("Login");

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

let Sign = document.getElementById("SignIn/Up");
let SignIn = document.getElementById("SignIn");
let SignUp = document.getElementById("SignUp");
document.getElementById("SignIn/Up").addEventListener("click", function() {
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

// -------========-------    Front Page    -------========-------
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
      const items = files.map((f, idx) => `<li class="list-group-item">${idx + 1}. ${f.name}</li>`).join("");
      selectedFilesBox.innerHTML = `
        <div class="alert alert-info p-2 mb-2" role="status">
          Selected ${files.length} file${files.length > 1 ? 's' : ''}
        </div>
        <ul class="list-group">${items}</ul>`;
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
          <h5>✓ Email Analysis Complete - ID: ${data.email_id}</h5>
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
      
      // Show download button after successful analysis
      if (downloadSection) downloadSection.classList.remove("hidden");
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

// -------========-------    Forum Page Discussion Selection    -------========-------
// Discussion data (placeholder content!!)
const discussions = {
  "Discussion 1": {
    author: "FishMaster92",
    time: "(x) time ago",
    views: 100,
    replies: 10,
    likes: 10,
    content: `<p>here will the text be</p>`
  },
  "Discussion 2": {
    author: "ProAngler",
    time: "(x) time ago",
    views: 100,
    replies: 10,
    likes: 10,
    content: `<p>here will the text be</p>`
  },
  "Discussion 3": {
    author: "AdminTeam",
    time: "(x) time ago",
    views: 100,
    replies: 10,
    likes: 10,
    content: `<p>here will the text be</p>`
  },
  "Discussion 4": {
    author: "IceFisher88",
    time: "(x) time ago",
    views: 100,
    replies: 10,
    likes: 10,
    content: `<p>here will the text be</p>`
  },
  "Discussion 5": {
    author: "GreenAngler",
    time: "(x) time ago",
    views: 100,
    replies: 10,
    likes: 10,
    content: `<p>here will the text be</p>`
  }
};

// Add click handlers to discussion items
const topicItems = document.querySelectorAll('.topic-item');
topicItems.forEach(item => {
  item.addEventListener('click', function() {
    // Remove active class from all items
    topicItems.forEach(i => i.classList.remove('active'));
    
    // Add active class to clicked item
    this.classList.add('active');
    
    // Get the discussion title
    const title = this.querySelector('.discussion-title').textContent;
    
    // Get the discussion data
    const discussion = discussions[title];
    
    if (discussion) {
      // Build the discussion HTML
      const discussionHTML = `
        <div class="discussion-header">
          <h2 class="discussion-title-large">${title}</h2>
          <p class="topic-meta">Posted by ${discussion.author} • ${discussion.time}</p>
          <div class="discussion-stats">
            <span class="stat-item"> ${discussion.replies} replies</span>
            <span class="stat-item"> ${discussion.likes} likes</span>
          </div>
        </div>
        <div class="discussion-body">
          ${discussion.content}
        </div>
        <div class="reply-section">
          <h3>Replies</h3>
          <p class="placeholder-text">Discussion replies would appear here...</p>
        </div>
      `;
      
      // Update the discussion content area
      document.getElementById('discussion-content').innerHTML = discussionHTML;
    }
  });
});
