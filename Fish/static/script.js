// -------========-------    Sign Up    -------========-------

let login = document.getElementById("LoginContainer");
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
  login.style.display = "None";
});

// --- Sign in/up toggle  ---
let Sign = document.getElementById("SignIn/Up");
let SignIn = document.getElementById("SignIn");
let SignUp = document.getElementById("SignUp");

 
// Global password validation helpers (Uses signup and change password)
function validatePasswordRules(pw) {
  return {
    length: typeof pw === 'string' && pw.length >= 8,
    lower: /[a-z]/.test(pw),
    upper: /[A-Z]/.test(pw),
    number: /[0-9]/.test(pw),
    symbol: /[^A-Za-z0-9]/.test(pw)
  };
}

// Update the password requirements UI
function updateRequirementsUI(pw, prefix = '') {
  const rules = validatePasswordRules(pw);
  const id = (name) => prefix ? `${prefix}-${name}` : name;
  const set = (idName, ok, text) => {
    const el = document.getElementById(id(idName));
    if (!el) return;
    el.textContent = (ok ? '✅ ' : '❌ ') + text;
    el.style.color = ok ? '#198754' : '';
  };
  set('req-length', rules.length, 'At least 8 characters (recommended 16+)');
  set('req-lower', rules.lower, 'Contains a lowercase letter');
  set('req-upper', rules.upper, 'Contains an uppercase letter');
  set('req-number', rules.number, 'Contains a number');
  set('req-symbol', rules.symbol, 'Contains a symbol');
}

function updateMatchUI(pw, confirm, prefix = '') {
  const matchEl = document.getElementById(prefix ? `${prefix}-password-match` : 'password-match');
  if (!matchEl) return;
  if ((pw || '').length === 0 && (confirm || '').length === 0) {
    matchEl.style.display = 'none';
    return;
  }
  if (pw === confirm) {
    matchEl.textContent = '✅ Passwords match';
    matchEl.style.color = '#198754';
    matchEl.style.display = 'block';
  } else {
    matchEl.textContent = '❌ Passwords do not match';
    matchEl.style.color = '';
    matchEl.style.display = 'block';
  }
}

if (Sign && SignIn && SignUp) {
  Sign.addEventListener("click", function() {
    SignIn.classList.toggle("hidden");
    SignUp.classList.toggle("hidden");
    Sign.classList.toggle("btn-dark");
    Sign.classList.toggle("btn-secondary");
  });
  

  // Wire realtime updates if inputs exist
  const pwInput = document.getElementById('pass-req');
  const pwConfirm = document.getElementById('pass-ver');
  if (pwInput) {
    pwInput.addEventListener('input', (e) => {
      updateRequirementsUI(e.target.value || '');
      updateMatchUI(e.target.value || '', pwConfirm ? pwConfirm.value || '' : '');
    });
  }
  if (pwConfirm) {
    pwConfirm.addEventListener('input', (e) => {
      updateMatchUI(pwInput ? pwInput.value || '' : '', e.target.value || '');
    });
  }

  // Signup submit handler with client-side validation
  SignUp.onsubmit = async (e) => {
    e.preventDefault();

    const signupErrorDiv = document.getElementById('signupError');
    if (signupErrorDiv) {
      signupErrorDiv.style.display = 'none';
      signupErrorDiv.innerHTML = '';
    }

    const password = pwInput ? pwInput.value || '' : '';
    const confirm = pwConfirm ? pwConfirm.value || '' : '';
    const rules = validatePasswordRules(password);

    const allRules = rules.length && rules.lower && rules.upper && rules.number && rules.symbol;
    const passwordsMatch = password === confirm && password.length > 0;

    if (!allRules || !passwordsMatch) {
      // Show friendly error message and do not submit
      let msgs = [];
      if (!rules.length) msgs.push('Password must be at least 8 characters (16+ recommended).');
      if (!rules.lower) msgs.push('Include at least one lowercase letter.');
      if (!rules.upper) msgs.push('Include at least one uppercase letter.');
      if (!rules.number) msgs.push('Include at least one number.');
      if (!rules.symbol) msgs.push('Include at least one symbol (e.g. !@#$%).');
      if (!passwordsMatch) msgs.push('Passwords do not match.');

      if (signupErrorDiv) {
        signupErrorDiv.innerHTML = `<div class="alert alert-danger" role="alert"><strong>Cannot create account:</strong><ul style=\"margin:0;padding-left:1rem;\">${msgs.map(m=>`<li>${m}</li>`).join('')}</ul></div>`;
        signupErrorDiv.style.display = 'block';
      } else {
        alert('Signup validation failed: ' + msgs.join(' '));
      }
      // update UI checklist
      updateRequirementsUI(password);
      updateMatchUI(password, confirm);
      return;
    }

    // If valid, proceed with previous submit behaviour
    let SignUpForm = new FormData(e.target);
    let SignUpResponse = await fetch("/Signup", { method: "POST", body: SignUpForm });
    let SignUpData = await SignUpResponse.json();
    if (SignUpData.success) {
      window.open(window.location.href, "_self");
    } else {
      signupErrorDiv.innerHTML = `<strong>Error:</strong> ${SignUpData.error || SignUpData.message || "Failed to create account"}`;
      signupErrorDiv.style.display = "block";
    }
  };
  SignIn.onsubmit = async (e) => {
    e.preventDefault();
    const signinErrorDiv = document.getElementById("SignInError");
    signinErrorDiv.style.display = "none";

    let SignInForm = new FormData(e.target);
    let SignInResponse = await fetch("/login", { method: "POST", body: SignInForm });
    let SignInData = await SignInResponse.json();

    if (SignInData.success) {
      window.open(window.location.href, "_self");
    } else {
      signinErrorDiv.innerHTML = `<strong>Error:</strong> ${SignInData.error || SignInData.message || "Incorect username or password"}`;
      signinErrorDiv.style.display = "block";
    }
  };
}

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
      
      // Tag options for dropdowns
      const tagOptions = [
        "Account Notice", "Payment/Invoice", "Security Alert", "Password Reset", "Shipping/Delivery",
        "Subscription", "Promotion/Offer", "Job Alert", "Social Notification", "Banking",
        "Legal/Policy", "System Alert", "Survey/Feedback", "News/Newsletter", "Authentication",
        "Two-Factor", "Travel/Booking", "Support/Ticket", "Confirmation/Receipt", "Other"
      ];
      
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
            <div class="fw-semibold text-truncate" title="${f.name}">
              ${f.name.trim().substring(0, 25)}${f.name.trim().length > 25 ? '...' : ''}
            </div>
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

          <div class="mt-2">
            <label for="tag-${idx}" class="form-label small mb-1" style="color: rgba(238,238,238,0.8);">Category:</label>
            <div class="d-flex gap-2 align-items-center">
              <select name="tags[]" id="tag-${idx}" class="form-control form-control-sm flex-grow-1">
                <option value="">-- Select a category --</option>
                ${tagOptions.map(tag => `<option value="${tag.replace(/"/g, '&quot;')}">${tag}</option>`).join('')}
              </select>
              <span class="suggest-tag-hint small text-muted" data-index="${idx}" style="white-space: nowrap;"></span>
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

        // Helper: display suggested tag from upload response
        function displayTagSuggestion(fileIndex, suggestedTag) {
          const hint = document.querySelector(`.suggest-tag-hint[data-index="${fileIndex}"]`);
          if (!hint || !suggestedTag) return;
          hint.textContent = `Suggested: ${suggestedTag}`;
          hint.style.color = 'rgba(200,220,255,0.9)';
          // Optionally auto-select the suggested tag in the dropdown
          const select = document.getElementById(`tag-${fileIndex}`);
          if (select) {
            select.value = suggestedTag;
          }
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

    // Ask about forum creation
    askAboutForum = []
    
    // Validate file type and size
    for (let i = 0; i < fileInput.files.length; i++) {
      const file = fileInput.files[i];
      askAboutForum.push(true)
      
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

    // Show analysis section and hide sidebars IMMEDIATELY
    toggleAnalysis();
    hideSidebars();
    
    const downloadSection = document.getElementById("downloadSection");
    if (downloadSection) downloadSection.classList.add("hidden");

    // Show progress page IMMEDIATELY (before upload completes)
    document.getElementById("result").innerHTML = `
      <div class="row">
        <div class="col-md-8">
          <div class="alert alert-info" role="alert">
            <h5>Uploading and Analyzing Email...</h5>
            <p class="mb-0">Please wait while we process your file.</p>
          </div>

          <div id="virusSection" class="mt-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
                <div class="text-center my-3">
                  <div class="spinner-border text-info" role="status">
                    <span class="visually-hidden">Waiting...</span>
                  </div>
                  <p class="mt-2 text-muted">Waiting to start...</p>
                </div>
              </div>
            </div>
          </div>

          <div id="ipSection" class="mt-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
                <div class="text-center my-3">
                  <div class="spinner-border text-warning" role="status">
                    <span class="visually-hidden">Waiting...</span>
                  </div>
                  <p class="mt-2 text-muted">Waiting to start...</p>
                </div>
              </div>
            </div>
          </div>

          <div id="llmSection" class="mt-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
                <div class="text-center my-3">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Waiting...</span>
                  </div>
                  <p class="mt-2 text-muted">Waiting to start...</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-3 text-muted">Analysis Progress</h6>

              <div id="vtProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">VirusTotal analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="vtProgressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-info" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>

              <div id="abuseProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">AbuseIPDb analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="abuseProgressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-warning" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>

              <div id="llmProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">LLM analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="llmProgressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    `;

    // Capture the checkbox state before upload
    const useAICheckbox = document.getElementById("useAI");
    const useAI = useAICheckbox ? useAICheckbox.checked : false;
    
    // Store AI preference globally so it can be accessed by analysis functions
    window.useAI = useAI;
    
    // Collect tag selections from dropdowns
    const tagSelects = document.querySelectorAll('select[name="tags[]"]');
    const selectedTags = Array.from(tagSelects).map(select => select.value || '');
    
    // Now initiate the upload
    let formData = new FormData(e.target);
    // Remove any existing tags[] entries and re-add with selected values
    // (FormData doesn't let us easily update, so we reconstruct)
    const files = fileInput.files;
    const comments = Array.from(document.querySelectorAll('.comment-input')).map(inp => inp.value || '');
    const useAIVal = useAICheckbox ? useAICheckbox.checked : false;
    
    // Create a new FormData with explicit ordering
    const newFormData = new FormData();
    for (let i = 0; i < files.length; i++) {
      newFormData.append('file', files[i]);
    }
    for (let i = 0; i < comments.length; i++) {
      newFormData.append('comments[]', comments[i]);
    }
    for (let i = 0; i < selectedTags.length; i++) {
      newFormData.append('tags[]', selectedTags[i]);
    }
    if (useAIVal) {
      newFormData.append('use_ai', '1');
    }
    
    let respons = await fetch("/upload", { method: "POST", body: newFormData });
    let data = await respons.json();
    
    // Handle error response
    if (data.error || !data.success) {
      document.getElementById("result").innerHTML = 
        `<div class="alert alert-danger" role="alert"><strong>Upload Failed:</strong> ${data.error || data.message || 'Unknown error occurred'}</div>`;
      return;
    }
    
    // Store all files data globally for tab switching
    // Fix: Server returns files at data.data.files, not data.files
    window.uploadedFiles = (data.data && data.data.files) || [];
    window.currentFileIndex = 0;
    window.fileAnalysisResults = {}; // Store analysis results per file
    
    // Display suggested tags from the upload response (after server processes)
    if (data.data && data.data.files && Array.isArray(data.data.files)) {
      data.data.files.forEach((file, idx) => {
        if (file.data && file.data.suggested_tag) {
          displayTagSuggestion(idx, file.data.suggested_tag);
        }
      });
    }
    
    // Update the header to show success - render first file and start its analysis
    if (data.success && window.uploadedFiles.length > 0) {
      renderFileAnalysis(0);
      for (let i = 0; i < fileInput.files.length; i++) {
        await runFileAnalyses(i);
      }
    }
  };
}

// -------========-------    File Tab Switching Function    -------========-------
async function switchFileTab(fileIndex) {
  if (!window.uploadedFiles || fileIndex < 0 || fileIndex >= window.uploadedFiles.length) {
    return;
  }
  
  window.currentFileIndex = fileIndex;
  
  // Update tab button states
  const tabButtons = document.querySelectorAll('.account-toggle-buttons .toggle-btn');
  tabButtons.forEach((btn, idx) => {
    if (idx === fileIndex) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  
  // Check if we have cached results for this file (in-memory)
  if (window.fileAnalysisResults[fileIndex]) {
    // Display cached results
    displayCachedResults(fileIndex);
    return;
  }
  
  // Try to load from localStorage
  const file = window.uploadedFiles[fileIndex];
  const emailId = file.email_id;
  
  if (emailId) {
    const localData = loadAnalysisFromLocalStorage(emailId);
    if (localData && localData.virusTotal && localData.abuseIP && localData.llm) {
      // Found in localStorage - cache and display
      window.fileAnalysisResults[fileIndex] = localData;
      displayCachedResults(fileIndex);
      return;
    }
    
    // Try to load from backend database
    const backendData = await loadAnalysisFromBackend(emailId);
    if (backendData && backendData.details) {
      // Found in backend - reconstruct UI from backend data
      reconstructAnalysisFromBackend(fileIndex, backendData);
      return;
    }
  }
  
  // No cached data found - render loading state and run analyses
  renderFileAnalysis(fileIndex);
  runFileAnalyses(fileIndex);
}

// -------========-------    Update Progress Bars for File    -------========-------
function updateProgressBarsForFile(fileIndex, isComplete) {
  // Get or initialize progress state for this file
  if (!window.fileProgressStates) {
    window.fileProgressStates = {};
  }
  
  const progressState = window.fileProgressStates[fileIndex] || {
    virusTotal: 0,
    abuseIP: 0,
    llm: 0
  };
  
  // Update VirusTotal progress bar
  const vtBar = document.getElementById("vtProgressBar");
  if (vtBar) {
    if (isComplete || progressState.virusTotal === 100) {
      vtBar.style.width = "100%";
      vtBar.setAttribute("aria-valuenow", 100);
      vtBar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-info");
      vtBar.classList.add("bg-success");
      vtBar.textContent = "Completed";
    } else if (progressState.virusTotal === -1) {
      vtBar.style.width = "100%";
      vtBar.setAttribute("aria-valuenow", 100);
      vtBar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-info");
      vtBar.classList.add("bg-danger");
      vtBar.textContent = "Failed";
    } else {
      vtBar.style.width = progressState.virusTotal + "%";
      vtBar.setAttribute("aria-valuenow", progressState.virusTotal);
      vtBar.textContent = progressState.virusTotal > 0 ? "In Progress..." : "0%";
    }
  }
  
  // Update AbuseIPDB progress bar
  const abuseBar = document.getElementById("abuseProgressBar");
  if (abuseBar) {
    if (isComplete || progressState.abuseIP === 100) {
      abuseBar.style.width = "100%";
      abuseBar.setAttribute("aria-valuenow", 100);
      abuseBar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-warning");
      abuseBar.classList.add("bg-success");
      abuseBar.textContent = "Completed";
    } else if (progressState.abuseIP === -1) {
      abuseBar.style.width = "100%";
      abuseBar.setAttribute("aria-valuenow", 100);
      abuseBar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-warning");
      abuseBar.classList.add("bg-danger");
      abuseBar.textContent = "Failed";
    } else {
      abuseBar.style.width = progressState.abuseIP + "%";
      abuseBar.setAttribute("aria-valuenow", progressState.abuseIP);
      abuseBar.textContent = progressState.abuseIP > 0 ? "In Progress..." : "0%";
    }
  }
  
  // Update LLM progress bar
  const llmBar = document.getElementById("llmProgressBar");
  if (llmBar) {
    if (isComplete || progressState.llm === 100) {
      llmBar.style.width = "100%";
      llmBar.setAttribute("aria-valuenow", 100);
      llmBar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-primary");
      llmBar.classList.add("bg-success");
      llmBar.textContent = "Completed";
    } else if (progressState.llm === -1) {
      llmBar.style.width = "100%";
      llmBar.setAttribute("aria-valuenow", 100);
      llmBar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-primary");
      llmBar.classList.add("bg-danger");
      llmBar.textContent = "Failed";
    } else {
      llmBar.style.width = progressState.llm + "%";
      llmBar.setAttribute("aria-valuenow", progressState.llm);
      llmBar.textContent = progressState.llm > 0 ? "In Progress..." : "0%";
    }
  }
}

// -------========-------    Display Cached Results    -------========-------
function displayCachedResults(fileIndex) {
  const file = window.uploadedFiles[fileIndex];
  const cached = window.fileAnalysisResults[fileIndex];
  const status = cached.status || { virusTotal: true, abuseIP: true, llm: true };
  
  // Determine progress bar states based on actual success/failure
  const vtBarClass = status.virusTotal ? 'bg-success' : 'bg-danger';
  const vtBarText = status.virusTotal ? 'Completed' : 'Failed';
  
  const abuseBarClass = status.abuseIP ? 'bg-success' : 'bg-danger';
  const abuseBarText = status.abuseIP ? 'Completed' : 'Failed';
  
  const llmBarClass = status.llm ? 'bg-success' : 'bg-danger';
  const llmBarText = status.llm ? 'Completed' : 'Failed';
  
  // Update the content area with cached results AND progress bars
  const contentArea = document.getElementById("analysisContent");
  if (askAboutForum[fileIndex]) {
    AskToCreateForum(fileIndex);
  }
  if (contentArea) {
    contentArea.innerHTML = `
      <div class="row">
        <div class="col-md-8">
          ${cached.virusTotal || ''}
          ${cached.abuseIP || ''}
          ${cached.llm || ''}
        </div>

        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-3 text-muted">Analysis Progress</h6>

              <div id="vtProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">VirusTotal analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="vtProgressBar" class="progress-bar ${vtBarClass}" 
                       role="progressbar" style="width: 100%;" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">${vtBarText}</div>
                </div>
              </div>

              <div id="abuseProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">AbuseIPDb analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="abuseProgressBar" class="progress-bar ${abuseBarClass}" 
                       role="progressbar" style="width: 100%;" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">${abuseBarText}</div>
                </div>
              </div>

              <div id="llmProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">LLM analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="llmProgressBar" class="progress-bar ${llmBarClass}" 
                       role="progressbar" style="width: 100%;" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">${llmBarText}</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    `;
  }
}

// -------========-------    Render File Analysis    -------========-------
function renderFileAnalysis(fileIndex) {
  const file = window.uploadedFiles && window.uploadedFiles[fileIndex];
  if (!file) {
    console.warn('renderFileAnalysis: file not found for index', fileIndex);
    return;
  }

  // Ensure we have a result container. Create one inside #analysis if missing.
  let resultDiv = document.getElementById("result");
  const analysisEl = (typeof analysis !== 'undefined' && analysis) ? analysis : document.getElementById("analysis");

  if (!resultDiv) {
    if (analysisEl) {
      resultDiv = document.createElement('div');
      resultDiv.id = 'result';
      analysisEl.appendChild(resultDiv);
    } else {
      console.warn('renderFileAnalysis: no #result and no #analysis element found; aborting render');
      return;
    }
  }

  // Check for existing tabs inside the (now guaranteed) resultDiv
  const existingTabs = resultDiv.querySelector('.account-toggle-buttons');

  if (!existingTabs) {
    let tabsHTML = '';
    if (window.uploadedFiles && window.uploadedFiles.length > 1) {
      tabsHTML = `
        <div class="account-toggle-buttons" style="margin-bottom: 1rem;">
          ${window.uploadedFiles.map((f, idx) => `
            <button class="toggle-btn ${idx === fileIndex ? 'active' : ''}" onclick="switchFileTab(${idx})">
              ${f.filename || `File ${idx + 1}`}
            </button>
          `).join('')}
        </div>
      `;
    }

    resultDiv.innerHTML = tabsHTML + `<div id="analysisContent"></div>`;
  }
  AskToCreateForum(0)

  // Update only the content area
  const contentArea = document.getElementById("analysisContent");
  if (contentArea) {
    contentArea.innerHTML = `
      <div class="row">
        <div class="col-md-8">
          <div id="virusSection" class="mt-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
                <div class="text-center my-3">
                  <div class="spinner-border text-info" role="status">
                    <span class="visually-hidden">Waiting...</span>
                  </div>
                  <p class="mt-2 text-muted">Waiting to start...</p>
                </div>
              </div>
            </div>
          </div>

          <div id="ipSection" class="mt-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
                <div class="text-center my-3">
                  <div class="spinner-border text-warning" role="status">
                    <span class="visually-hidden">Waiting...</span>
                  </div>
                  <p class="mt-2 text-muted">Waiting to start...</p>
                </div>
              </div>
            </div>
          </div>

          <div id="llmSection" class="mt-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
                <div class="text-center my-3">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Waiting...</span>
                  </div>
                  <p class="mt-2 text-muted">Waiting to start...</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-3 text-muted">Analysis Progress</h6>

              <div id="vtProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">VirusTotal analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="vtProgressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-info" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>

              <div id="abuseProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">AbuseIPDb analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="abuseProgressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-warning" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>

              <div id="llmProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">LLM analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="llmProgressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    `;
  }
}

// -------========-------    Persistence Helper Functions    -------========-------
// Save analysis results to localStorage
function saveAnalysisToLocalStorage(emailId, analysisData) {
  try {
    const storageKey = `analysis_${emailId}`;
    localStorage.setItem(storageKey, JSON.stringify(analysisData));
  } catch (e) {
    console.warn('Failed to save to localStorage:', e);
  }
}

// Load analysis results from localStorage
function loadAnalysisFromLocalStorage(emailId) {
  try {
    const storageKey = `analysis_${emailId}`;
    const data = localStorage.getItem(storageKey);
    return data ? JSON.parse(data) : null;
  } catch (e) {
    console.warn('Failed to load from localStorage:', e);
    return null;
  }
}

// Save analysis results to backend database
async function saveAnalysisToBackend(emailId) {
  try {
    const response = await fetch('/api/scan-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email_id: emailId })
    });
    
    const data = await response.json();
    return data.success;
  } catch (e) {
    console.warn('Failed to save analysis to backend:', e);
    return false;
  }
}

// Load analysis results from backend database
async function loadAnalysisFromBackend(emailId) {
  try {
    const response = await fetch(`/api/analysis/${emailId}`);
    const data = await response.json();
    
    if (data.success && data.analysis) {
      return data.analysis;
    }
    return null;
  } catch (e) {
    console.warn('Failed to load analysis from backend:', e);
    return null;
  }
}

// Reconstruct analysis UI from backend data
function reconstructAnalysisFromBackend(fileIndex, backendData) {
  const details = backendData.details;
  
  // Build VirusTotal section
  let vtHTML = '';
  if (details.virustotal && !details.virustotal.error) {
    const stats = details.virustotal.stats || {};
    const malicious = stats.malicious || 0;
    const suspicious = stats.suspicious || 0;
    const harmless = stats.harmless || 0;
    const undetected = stats.undetected || 0;
    const totalScans = stats.total_scans || 0;
    
    let threatLevel = "Clean";
    let threatClass = "success";
    let threatIcon = "[SAFE]";
    
    if (malicious > 0) {
      threatLevel = "Malicious";
      threatClass = "danger";
      threatIcon = "[ALERT]";
    } else if (suspicious > 0) {
      threatLevel = "Suspicious";
      threatClass = "warning";
      threatIcon = "[WARNING]";
    }
    
    const detectionRate = totalScans > 0 ? ((malicious + suspicious) / totalScans * 100).toFixed(1) : 0;
    
    vtHTML = `
      <div id="virusSection" class="mt-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
            <div class="alert alert-${threatClass} mb-0">
              <h6>${threatIcon} File Scan Results</h6>
              <hr>
              <div class="row">
                <div class="col-md-6">
                  <p><strong>Threat Level:</strong> <span class="badge bg-${threatClass}">${threatLevel}</span></p>
                  <p><strong>Detection Rate:</strong> ${detectionRate}% (${malicious + suspicious}/${totalScans})</p>
                  <p><strong>File Type:</strong> ${details.virustotal.file_type || 'Unknown'}</p>
                </div>
                <div class="col-md-6">
                  <p><strong>Malicious:</strong> <span class="badge bg-danger">${malicious}</span></p>
                  <p><strong>Suspicious:</strong> <span class="badge bg-warning">${suspicious}</span></p>
                  <p><strong>Harmless:</strong> <span class="badge bg-success">${harmless}</span></p>
                  <p><strong>Undetected:</strong> <span class="badge bg-secondary">${undetected}</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    vtHTML = `
      <div id="virusSection" class="mt-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
            <div class="alert alert-warning mb-0">
              <strong>VirusTotal Unavailable:</strong> ${details.virustotal?.error || 'No data available'}
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  // Build AbuseIPDB section
  let ipHTML = '';
  if (details.abuseipdb && !details.abuseipdb.error) {
    const abuseScore = details.abuseipdb.abuse_score || 0;
    
    let riskLevel = "Low";
    let riskClass = "success";
    let riskIcon = "[OK]";
    
    if (abuseScore >= 50) {
      riskLevel = "High";
      riskClass = "danger";
      riskIcon = "[!]";
    } else if (abuseScore >= 25) {
      riskLevel = "Medium";
      riskClass = "warning";
      riskIcon = "[!]";
    }
    
    ipHTML = `
      <div id="ipSection" class="mt-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
            <div class="alert alert-${riskClass} mb-0">
              <h6>${riskIcon} Sender IP Reputation</h6>
              <hr>
              <div class="row">
                <div class="col-md-6">
                  <p><strong>Risk Level:</strong> <span class="badge bg-${riskClass}">${riskLevel}</span></p>
                  <p><strong>Abuse Score:</strong> ${abuseScore}/100</p>
                  <p><strong>Total Reports:</strong> ${details.abuseipdb.total_reports || 0}</p>
                </div>
                <div class="col-md-6">
                  <p><strong>Country:</strong> ${details.abuseipdb.country_code || 'N/A'}</p>
                  <p><strong>ISP:</strong> ${details.abuseipdb.isp || 'N/A'}</p>
                  <p><strong>Usage Type:</strong> ${details.abuseipdb.usage_type || 'N/A'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    ipHTML = `
      <div id="ipSection" class="mt-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
            <div class="alert alert-warning mb-0">
              <strong>IP Check Unavailable:</strong> ${details.abuseipdb?.error || 'No data available'}
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  // Build LLM section
  let llmHTML = '';
  if (details.llm && !details.llm.error) {
    llmHTML = `
      <div id="llmSection" class="mt-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
            <div class="alert alert-primary mb-0">
              <h6>[ANALYSIS] Phishing Analysis Results</h6>
              <hr>
              <div style="white-space: pre-wrap;">${details.llm.response || 'Analysis completed'}</div>
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    llmHTML = `
      <div id="llmSection" class="mt-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
            <div class="alert alert-warning mb-0">
              <strong>Analysis Unavailable:</strong> ${details.llm?.error || 'No data available'}
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  // Cache the reconstructed data
  window.fileAnalysisResults[fileIndex] = {
    virusTotal: vtHTML,
    abuseIP: ipHTML,
    llm: llmHTML,
    status: {
      virusTotal: !!(details.virustotal && !details.virustotal.error),
      abuseIP: !!(details.abuseipdb && !details.abuseipdb.error),
      llm: !!(details.llm && !details.llm.error)
    },
    emailId: backendData.email_id
  };
  
  // Save to localStorage for faster future access
  saveAnalysisToLocalStorage(backendData.email_id, window.fileAnalysisResults[fileIndex]);
  
  // Display the reconstructed results
  displayCachedResults(fileIndex);
}

function AskToCreateForum(fileIndex) {
  askAboutForum[fileIndex] = false;

  const container = document.getElementById("result");
  html = `<div id="AskCreateForum" class="centered backdrop">
      <div id="AskForForumForm" class="centered colored-border">
        <button id="CloseQuestion" type="button" class="close-btn">✕</button>
        <h1 class="page-title">Get Community Feedback</h1>
        <p>Would you like to shear your email wiht the comunity?</p>
        <p>To get a better understanding of what threats you might be facing, there is no place better our Forum.</p>
        <p>Create a Forum post to see what to community has to say about your situation.</p>
        <form>
          <h3 class="section-header">Do You Want to Create a Forum post?</h2>
          <div id="forumForm" class="form-check form-switch">
            <label for="Yes"><input type="radio" id="Yes" value="Yes" name="CreateForum" class="form-check-input" required>
            Yes</label>

            <label for="No"><input type="radio" id="No" value="No" name="CreateForum" class="form-check-input" required>
            No</label>
          </div>
          <button type="submit" class="submit-btn">Submitt</button>
        </form>
      </div>
    </div>`;
  container.insertAdjacentHTML("beforebegin", html);

  document.getElementById("CloseQuestion").addEventListener("click", function() {
    document.getElementById("AskCreateForum").remove();
  });
  document.getElementById("AskCreateForum").getElementsByTagName("form")[0].onsubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const answer = formData.get("CreateForum");

    if (answer == "Yes") {
      Forum_Creator(e);
      document.getElementById("AskCreateForum").remove();
    } else {
      document.getElementById("AskCreateForum").remove();
    }
  };
}

// -------========-------    Run File Analyses    -------========-------
function runFileAnalyses(fileIndex) {
  const file = window.uploadedFiles[fileIndex];
  const bodyText = file.data.body_text?.trim() || 'No content';
  const senderIp = file.data.sender_ip || "";
  const emailId = file.email_id;

  // Helper function to update progress bar
  function updateProgress(barId, status) {
    const bar = document.getElementById(barId);
    if (!bar) return;
    
    if (status === 'start') {
      bar.style.width = "30%";
      bar.setAttribute("aria-valuenow", 30);
      bar.textContent = "In Progress...";
      bar.classList.add("progress-bar-animated", "progress-bar-striped");
    } else if (status === 'complete') {
      bar.style.width = "100%";
      bar.setAttribute("aria-valuenow", 100);
      bar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-info", "bg-warning", "bg-primary");
      bar.classList.add("bg-success");
      bar.textContent = "Completed";
    } else if (status === 'error') {
      bar.style.width = "100%";
      bar.setAttribute("aria-valuenow", 100);
      bar.classList.remove("progress-bar-animated", "progress-bar-striped", "bg-info", "bg-warning", "bg-primary");
      bar.classList.add("bg-danger");
      bar.textContent = "Failed";
    }
  }

  // Track completion of all analyses
  let completedCount = 0;
  const totalAnalyses = 3;
  
  // Track success/failure status for each API
  const analysisStatus = {
    virusTotal: false,
    abuseIP: false,
    llm: false
  };
  
  // Store raw API results for backend storage
  const apiResults = {
    virusTotal: null,
    abuseIP: null,
    llm: null
  };
  
  function checkAllCompleted() {
    completedCount++;
    if (completedCount >= totalAnalyses) {
      // Cache the results for this file with status (in-memory)
      window.fileAnalysisResults[fileIndex] = {
        virusTotal: document.getElementById("virusSection").outerHTML,
        abuseIP: document.getElementById("ipSection").outerHTML,
        llm: document.getElementById("llmSection").outerHTML,
        status: analysisStatus,
        emailId: emailId
      };
      
      // Save to localStorage for quick client-side persistence
      saveAnalysisToLocalStorage(emailId, window.fileAnalysisResults[fileIndex]);
      
      // Save to backend database for long-term persistence
      // Note: The comprehensive scan endpoint will aggregate all results
      saveAnalysisToBackend(emailId);
    }
  }
  
  // VirusTotal API call with progress tracking
  if (emailId) {
    updateProgress("vtProgressBar", "start");
    callVirusTotalAPI(emailId).then((success) => {
      analysisStatus.virusTotal = success;
      if (success) {
        updateProgress("vtProgressBar", "complete");
      } else {
        updateProgress("vtProgressBar", "error");
      }
      checkAllCompleted();
    }).catch(() => {
      analysisStatus.virusTotal = false;
      updateProgress("vtProgressBar", "error");
      checkAllCompleted();
    });
  } else {
    analysisStatus.virusTotal = false;
    updateProgress("vtProgressBar", "error");
    checkAllCompleted();
  }
  
  // AbuseIPDB API call with progress tracking
  if (senderIp) {
    updateProgress("abuseProgressBar", "start");
    callAbuseIPAPI(senderIp).then((success) => {
      analysisStatus.abuseIP = success;
      if (success) {
        updateProgress("abuseProgressBar", "complete");
      } else {
        updateProgress("abuseProgressBar", "error");
      }
      checkAllCompleted();
    }).catch(() => {
      analysisStatus.abuseIP = false;
      updateProgress("abuseProgressBar", "error");
      checkAllCompleted();
    });
  } else {
    analysisStatus.abuseIP = false;
    updateProgress("abuseProgressBar", "error");
    checkAllCompleted();
  }
  
  // LLM API call with progress tracking - only if user enabled AI analysis
  if (window.useAI && bodyText) {
    updateProgress("llmProgressBar", "start");
    callLLMAPI(bodyText, emailId).then((success) => {
      analysisStatus.llm = success;
      if (success) {
        updateProgress("llmProgressBar", "complete");
      } else {
        updateProgress("llmProgressBar", "error");
      }
      checkAllCompleted();
    }).catch(() => {
      analysisStatus.llm = false;
      updateProgress("llmProgressBar", "error");
      checkAllCompleted();
    });
  } else if (!window.useAI) {
    // User did not enable AI analysis - skip it
    const llmSection = document.getElementById("llmSection");
    if (llmSection) {
      llmSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
            <div class="alert alert-info mb-0">
              <h6>[SKIPPED] AI Analysis Not Enabled</h6>
              <hr>
              <p class="mb-0">AI analysis was not requested. To enable AI-powered phishing detection, check the "Check submitted file with AI" option before uploading.</p>
            </div>
          </div>
        </div>
      `;
    }
    analysisStatus.llm = true; // Mark as "success" since it was intentionally skipped
    updateProgress("llmProgressBar", "complete");
    checkAllCompleted();
  } else {
    // No body text available
    analysisStatus.llm = false;
    updateProgress("llmProgressBar", "error");
    checkAllCompleted();
  }
}

// -------========-------    LLM API Call Function    -------========-------
async function callLLMAPI(bodyText, emailId, userComment = '') {
  const llmSection = document.getElementById("llmSection");
  
  if (!llmSection) return false;
  
  // Show loading state
  llmSection.innerHTML = `
    <div class="card">
      <div class="card-body">
        <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
        <div class="text-center my-3">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Analyzing...</span>
          </div>
          <p class="mt-2 text-muted">Analyzing email for phishing indicators...</p>
        </div>
      </div>
    </div>
  `;
  
  try {
    const llmResponse = await fetch("/api/llm", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        // message: bodyText,
        email_id: emailId,
        // comment: userComment
      })
    });
    
    // Handle non-200 responses gracefully
    let llmData;
    try {
      llmData = await llmResponse.json();
    } catch (parseError) {
      llmData = { 
        success: false, 
        error: `Server returned ${llmResponse.status}: Unable to parse response` 
      };
    }
    
    if (llmData.success && llmData.response) {
      // Display LLM analysis
      llmSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
            <div class="alert alert-primary mb-0">
              <h6>[ANALYSIS] Phishing Analysis Results</h6>
              <hr>
              <div style="white-space: pre-wrap;">${llmData.response}</div>
            </div>
          </div>
        </div>
      `;
      return true; // Success
    } else {
      // Display error with status code
      const errorMsg = llmData.error || llmData.message || 'Failed to analyze email';
      const statusCode = llmData.status_code || llmResponse.status;
      llmSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
            <div class="alert alert-warning mb-0">
              <strong>Analysis Unavailable (${statusCode}):</strong> ${errorMsg}
              <p class="mb-0 mt-2 small text-muted">The AI analysis service may be temporarily unavailable or rate-limited.</p>
            </div>
          </div>
        </div>
      `;
      return false; // Failed
    }
  } catch (error) {
    // Display network error
    llmSection.innerHTML = `
      <div class="card">
        <div class="card-body">
          <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
          <div class="alert alert-danger mb-0">
            <strong>Network Error:</strong> Failed to connect to analysis service
            <p class="mb-0 mt-2 small">${error.message}</p>
          </div>
        </div>
      </div>
    `;
    return false; // Failed
  }
}

// -------========-------    AbuseIPDB API Call Function    -------========-------
async function callAbuseIPAPI(ipAddress) {
  const ipSection = document.getElementById("ipSection");
  
  if (!ipSection) return false;
  
  // Show loading state
  ipSection.innerHTML = `
    <div class="card">
      <div class="card-body">
        <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
        <div class="text-center my-3">
          <div class="spinner-border text-warning" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Checking sender IP reputation...</p>
        </div>
      </div>
    </div>
  `;
  
  try {
    const ipResponse = await fetch("/api/check-ip", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ ip_address: ipAddress })
    });
    
    // Handle non-200 responses gracefully
    let ipData;
    try {
      ipData = await ipResponse.json();
    } catch (parseError) {
      ipData = { 
        success: false, 
        error: `Server returned ${ipResponse.status}: Unable to parse response` 
      };
    }
    
    if (ipData.success) {
      // Determine risk level and color
      let riskLevel = "Low";
      let riskClass = "success";
      let riskIcon = "[OK]";
      
      if (ipData.abuse_score >= 75) {
        riskLevel = "High";
        riskClass = "danger";
        riskIcon = "[!]";
      } else if (ipData.abuse_score >= 50) {
        riskLevel = "Medium";
        riskClass = "warning";
        riskIcon = "[!]";
      }
      
      // Display IP reputation analysis
      ipSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
            <div class="alert alert-${riskClass} mb-0">
              <h6>${riskIcon} Sender IP Reputation</h6>
              <hr>
              <div class="row">
                <div class="col-md-6">
                  <p><strong>IP Address:</strong> ${ipData.ip_address}</p>
                  <p><strong>Risk Level:</strong> <span class="badge bg-${riskClass}">${riskLevel}</span></p>
                  <p><strong>Abuse Score:</strong> ${ipData.abuse_score}/100</p>
                  <p><strong>Total Reports:</strong> ${ipData.total_reports}</p>
                </div>
                <div class="col-md-6">
                  <p><strong>Country:</strong> ${ipData.country_code}</p>
                  <p><strong>ISP:</strong> ${ipData.isp}</p>
                  <p><strong>Usage Type:</strong> ${ipData.usage_type}</p>
                  <p><strong>Whitelisted:</strong> ${ipData.is_whitelisted ? 'Yes' : 'No'}</p>
                </div>
              </div>
              ${ipData.is_malicious ? '<p class="mb-0 mt-2"><strong>[WARNING]</strong> This IP has been reported for malicious activity.</p>' : ''}
            </div>
          </div>
        </div>
      `;
      return true; // Success
    } else {
      // Display error or warning with status code
      const errorMsg = ipData.error || ipData.message || 'Unable to check IP reputation';
      const statusCode = ipData.status_code || ipResponse.status;
      ipSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
            <div class="alert alert-warning mb-0">
              <strong>IP Check Unavailable (${statusCode}):</strong> ${errorMsg}
              <p class="mb-0 mt-2 small text-muted">The IP reputation service may be temporarily unavailable or rate-limited.</p>
            </div>
          </div>
        </div>
      `;
      return false; // Failed
    }
  } catch (error) {
    // Display network error
    ipSection.innerHTML = `
      <div class="card">
        <div class="card-body">
          <h6 class="card-subtitle mb-2 text-muted">AbuseIPDB Analysis</h6>
          <div class="alert alert-danger mb-0">
            <strong>IP Check Error:</strong> Failed to connect to IP reputation service
            <p class="mb-0 mt-2 small">${error.message}</p>
          </div>
        </div>
      </div>
    `;
    return false; // Failed
  }
}

// -------========-------    VirusTotal API Call Function    -------========-------
async function callVirusTotalAPI(emailId) {
  const virusSection = document.getElementById("virusSection");
  
  if (!virusSection) return false;
  
  // Show loading state
  virusSection.innerHTML = `
    <div class="card">
      <div class="card-body">
        <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
        <div class="text-center my-3">
          <div class="spinner-border text-info" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Scanning file with VirusTotal...</p>
        </div>
      </div>
    </div>
  `;
  
  try {
    // First, try to get the file report (if file was already scanned)
    const reportResponse = await fetch("/api/file-report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email_id: emailId })
    });
    
    // Handle non-200 responses gracefully
    let reportData;
    try {
      reportData = await reportResponse.json();
    } catch (parseError) {
      reportData = { 
        success: false, 
        error: `Server returned ${reportResponse.status}: Unable to parse response`,
        status_code: reportResponse.status
      };
    }
    
    if (reportData.success && reportData.stats) {
      // File report available - display detailed results
      const stats = reportData.stats;
      const totalScans = stats.total_scans || 0;
      const malicious = stats.malicious || 0;
      const suspicious = stats.suspicious || 0;
      const undetected = stats.undetected || 0;
      const harmless = stats.harmless || 0;
      
      // Determine threat level
      let threatLevel = "Clean";
      let threatClass = "success";
      let threatIcon = "[SAFE]";
      
      if (malicious > 0) {
        threatLevel = "Malicious";
        threatClass = "danger";
        threatIcon = "[ALERT]";
      } else if (suspicious > 0) {
        threatLevel = "Suspicious";
        threatClass = "warning";
        threatIcon = "[WARNING]";
      }
      
      // Calculate detection percentage
      const detectionRate = totalScans > 0 ? ((malicious + suspicious) / totalScans * 100).toFixed(1) : 0;
      
      // Display VirusTotal scan results
      virusSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
            <div class="alert alert-${threatClass} mb-0">
              <h6>${threatIcon} File Scan Results</h6>
              <hr>
              <div class="row">
                <div class="col-md-6">
                  <p><strong>Threat Level:</strong> <span class="badge bg-${threatClass}">${threatLevel}</span></p>
                  <p><strong>Detection Rate:</strong> ${detectionRate}% (${malicious + suspicious}/${totalScans})</p>
                  <p><strong>File Type:</strong> ${reportData.file_type || 'Unknown'}</p>
                  <p><strong>File Size:</strong> ${(reportData.file_size / 1024).toFixed(2)} KB</p>
                </div>
                <div class="col-md-6">
                  <p><strong>Malicious:</strong> <span class="badge bg-danger">${malicious}</span></p>
                  <p><strong>Suspicious:</strong> <span class="badge bg-warning">${suspicious}</span></p>
                  <p><strong>Harmless:</strong> <span class="badge bg-success">${harmless}</span></p>
                  <p><strong>Undetected:</strong> <span class="badge bg-secondary">${undetected}</span></p>
                </div>
              </div>
              ${reportData.is_malicious ? '<p class="mb-0 mt-2"><strong>[ALERT] Warning:</strong> This file has been flagged as malicious by antivirus engines.</p>' : ''}
              ${reportData.file_hash ? `<p class="mb-0 mt-2"><small><strong>File Hash:</strong> <code>${reportData.file_hash.substring(0, 16)}...</code></small></p>` : ''}
            </div>
          </div>
        </div>
      `;
      return true; // Success
    } else {
      // Display error or warning with status code
      const errorMsg = reportData.error || reportData.message || 'Unable to retrieve scan results';
      const statusCode = reportData.status_code || reportResponse.status;
      virusSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
            <div class="alert alert-warning mb-0">
              <strong>VirusTotal Unavailable (${statusCode}):</strong> ${errorMsg}
              <p class="mb-0 mt-2 small text-muted">The file scanning service may be temporarily unavailable or rate-limited.</p>
            </div>
          </div>
        </div>
      `;
      return false; // Failed
    }
  } catch (error) {
    // Display network error
    virusSection.innerHTML = `
      <div class="card">
        <div class="card-body">
          <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
          <div class="alert alert-danger mb-0">
            <strong>VirusTotal Scan Error:</strong> Failed to connect to VirusTotal service
            <p class="mb-0 mt-2 small">${error.message}</p>
          </div>
        </div>
      </div>
    `;
    return false; // Failed
  }
}

function toggleAnalysis() {
  // Resolve elements at call time (page may not include the upload form)
  const UpFormLocal = UpForm || document.getElementById("uploadForm");
  const analysisLocal = analysis || document.getElementById("analysis");

  if (!analysisLocal) {
    console.warn("toggleAnalysis: analysis element not found - nothing to toggle");
    return;
  }

  // If upload form exists, toggle both states (original behaviour)
  if (UpFormLocal) {
    UpFormLocal.classList.toggle("hidden");
    analysisLocal.classList.toggle("hidden");

    // If upload form is visible now, we are returning to the upload view -> reset analysis UI
    if (!UpFormLocal.classList.contains("hidden")) {
      const loadingSpinner = document.getElementById("loadingSpinner");
      const downloadSection = document.getElementById("downloadSection");
      const resultDiv = document.getElementById("result");

      if (loadingSpinner) loadingSpinner.style.display = "none";
      if (downloadSection) downloadSection.classList.add("hidden");
      if (resultDiv) resultDiv.innerHTML = "";
    }
    // If upload form is hidden, we're in analysis view — nothing special to do
    return;
  }

  // No upload form on this page: just toggle the analysis panel visibility
  const isHidden = analysisLocal.classList.contains("hidden");
  if (isHidden) {
    analysisLocal.classList.remove("hidden");
  } else {
    // Hide analysis and try to reset internal analysis state if present
    const resultDiv = document.getElementById("result");
    const downloadSection = document.getElementById("downloadSection");
    const loadingSpinner = document.getElementById("loadingSpinner");

    if (resultDiv) resultDiv.innerHTML = "";
    if (downloadSection) downloadSection.classList.add("hidden");
    if (loadingSpinner) loadingSpinner.style.display = "none";

    analysisLocal.classList.add("hidden");
  }
}

const toUploadBtn = document.getElementById("ToUpload");
if (toUploadBtn) {
  toUploadBtn.addEventListener("click", toggleAnalysis);
}

// -------========-------    Sidebar Toggle Function    -------========-------
function toggleSidebar(side) {
  const layout = document.querySelector('.layout');
  const leftSidebar = document.getElementById('leftSidebar');
  const rightSidebar = document.getElementById('rightSidebar');
  const leftToggle = document.getElementById('leftToggle');
  const rightToggle = document.getElementById('rightToggle');
  const leftIcon = document.getElementById('leftToggleIcon');
  const rightIcon = document.getElementById('rightToggleIcon');
  
  if (side === 'left') {
    if (leftSidebar.classList.contains('collapsed')) {
      // Expand left sidebar
      leftSidebar.classList.remove('collapsed');
      layout.classList.remove('left-collapsed');
      leftIcon.textContent = '<';
    } else {
      // Collapse left sidebar
      leftSidebar.classList.add('collapsed');
      layout.classList.add('left-collapsed');
      leftIcon.textContent = '>';
    }
  } else if (side === 'right') {
    if (rightSidebar.classList.contains('collapsed')) {
      // Expand right sidebar
      rightSidebar.classList.remove('collapsed');
      layout.classList.remove('right-collapsed');
      rightIcon.textContent = '>';
    } else {
      // Collapse right sidebar
      rightSidebar.classList.add('collapsed');
      layout.classList.add('right-collapsed');
      rightIcon.textContent = '<';
    }
  }
}

// Function to hide both sidebars (used when starting analysis)
function hideSidebars() {
  const layout = document.querySelector('.layout');
  const leftSidebar = document.getElementById('leftSidebar');
  const rightSidebar = document.getElementById('rightSidebar');
  const leftIcon = document.getElementById('leftToggleIcon');
  const rightIcon = document.getElementById('rightToggleIcon');
  
  if (leftSidebar && !leftSidebar.classList.contains('collapsed')) {
    leftSidebar.classList.add('collapsed');
    layout.classList.add('left-collapsed');
    leftIcon.textContent = '>';
  }
  
  if (rightSidebar && !rightSidebar.classList.contains('collapsed')) {
    rightSidebar.classList.add('collapsed');
    layout.classList.add('right-collapsed');
    rightIcon.textContent = '<';
  }
}

document.addEventListener("DOMContentLoaded", function() {

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

  // -------========-------    Password Press-and-Hold Toggle    -------========-------
  const passwordInputs = [
    // Account settings
    { inputId: "currentPassword", buttonId: "toggleCurrentPassword" },
    { inputId: "newPassword", buttonId: "toggleNewPassword" },
    { inputId: "confirmPassword", buttonId: "toggleConfirmPassword" },
    // Login form
    { inputId: "pass", buttonId: "toggleLoginPassword" },
    // Signup form
    { inputId: "pass-req", buttonId: "toggleSignupPassword" },
    { inputId: "pass-ver", buttonId: "toggleSignupVerifyPassword" }
  ];

  passwordInputs.forEach(({ inputId, buttonId }) => {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    
    if (input && button) {
      // Show password on mouse down
      button.addEventListener("mousedown", function(e) {
        e.preventDefault();
        input.type = "text";
      });

      // Hide password on mouse up
      button.addEventListener("mouseup", function(e) {
        e.preventDefault();
        input.type = "password";
      });

      // Also hide if mouse leaves the button while holding
      button.addEventListener("mouseleave", function(e) {
        input.type = "password";
      });

      // Touch support for mobile
      button.addEventListener("touchstart", function(e) {
        e.preventDefault();
        input.type = "text";
      });

      button.addEventListener("touchend", function(e) {
        e.preventDefault();
        input.type = "password";
      });
    }
  });

  // -------========-------    Change Password Form    -------========-------
  const changePasswordForm = document.getElementById("changePasswordForm");
  if (changePasswordForm) {
    // Add realtime validation for change-password inputs
    const cpNew = document.getElementById('newPassword');
    const cpConfirm = document.getElementById('confirmPassword');
    if (cpNew) {
      cpNew.addEventListener('input', (ev) => {
        updateRequirementsUI(ev.target.value || '', 'acc');
        updateMatchUI(ev.target.value || '', cpConfirm ? cpConfirm.value || '' : '', 'acc');
      });
    }
    if (cpConfirm) {
      cpConfirm.addEventListener('input', (ev) => {
        updateMatchUI(cpNew ? cpNew.value || '' : '', ev.target.value || '', 'acc');
      });
    }

    changePasswordForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const currentPassword = document.getElementById("currentPassword").value;
      const newPassword = document.getElementById("newPassword").value;
      const confirmPassword = document.getElementById("confirmPassword").value;
      const errorDiv = document.getElementById("changePasswordError");
      const successDiv = document.getElementById("changePasswordSuccess");

      // Clear previous messages
      errorDiv.style.display = "none";
      successDiv.style.display = "none";
      errorDiv.innerHTML = "";
      successDiv.innerHTML = "";

      // Validation: Check all fields are filled
        if (!currentPassword || !newPassword || !confirmPassword) {
        errorDiv.innerHTML = `<div class="alert alert-danger alert-dismissible" role="alert">
            <strong>Error:</strong> All fields are required
            <button type="button" class="btn-close" aria-label="Close" onclick="this.parentElement.style.display='none'"></button>
          </div>`;
        errorDiv.style.display = "block";
        return;
      }

      // Validation: Check new passwords match
      if (newPassword !== confirmPassword) {
        errorDiv.innerHTML = `<div class="alert alert-danger alert-dismissible" role="alert">
            <strong>Error:</strong> New passwords do not match
            <button type="button" class="btn-close" aria-label="Close" onclick="this.parentElement.style.display='none'"></button>
          </div>`;
        errorDiv.style.display = "block";
        return;
      }

      // Validate strength rules
      const rules = validatePasswordRules(newPassword);
      const allRules = rules.length && rules.lower && rules.upper && rules.number && rules.symbol;
      if (!allRules) {
        let msgs = [];
        if (!rules.length) msgs.push('Password must be at least 8 characters (16+ recommended).');
        if (!rules.lower) msgs.push('Include at least one lowercase letter.');
        if (!rules.upper) msgs.push('Include at least one uppercase letter.');
        if (!rules.number) msgs.push('Include at least one number.');
        if (!rules.symbol) msgs.push('Include at least one symbol.');
        errorDiv.innerHTML = `<div class="alert alert-danger" role="alert"><strong>Cannot change password:</strong><ul style=\"margin:0;padding-left:1rem;\">${msgs.map(m=>`<li>${m}</li>`).join('')}</ul></div>`;
        errorDiv.style.display = 'block';
        // update UI checklist (account prefix)
        updateRequirementsUI(newPassword, 'acc');
        updateMatchUI(newPassword, confirmPassword, 'acc');
        return;
      }

      // Validation: Check old and new passwords are different
      if (currentPassword === newPassword) {
        errorDiv.innerHTML = `<div class="alert alert-danger alert-dismissible" role="alert">
            <strong>Error:</strong> New password must be different from current password
            <button type="button" class="btn-close" aria-label="Close" onclick="this.parentElement.style.display='none'"></button>
          </div>`;
        errorDiv.style.display = "block";
        return;
      }

      try {
        // Send change password request to server
        const formData = new FormData();
        formData.append("current_password", currentPassword);
        formData.append("new_password", newPassword);

        const response = await fetch("/change-password", {
          method: "POST",
          body: formData
        });

        const data = await response.json();

        if (data.success) {
          successDiv.innerHTML = `<div class="alert alert-success alert-dismissible fade show" role="alert">
              <strong>Success:</strong> Your password has been changed successfully.
              <button type="button" class="btn-close" aria-label="Close"></button>
            </div>`;
          successDiv.style.display = "block";
          // attach close handler
          const closeBtn = successDiv.querySelector('.btn-close');
          if (closeBtn) closeBtn.addEventListener('click', () => { successDiv.style.display = 'none'; });
          // scroll into view and reset form
          successDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
          changePasswordForm.reset();

          // Auto-hide after a short delay
          setTimeout(() => {
            const alertEl = successDiv.querySelector('.alert');
            if (alertEl) {
              alertEl.classList.remove('show');
              // hide container after fade
              setTimeout(() => { successDiv.style.display = 'none'; }, 300);
            } else {
              successDiv.style.display = 'none';
            }
          }, 4000);
        } else {
          errorDiv.innerHTML = `<div class="alert alert-danger alert-dismissible" role="alert">
              <strong>Error:</strong> ${data.error || data.message || "Failed to change password"}
              <button type="button" class="btn-close" aria-label="Close" onclick="this.parentElement.style.display='none'"></button>
            </div>`;
          errorDiv.style.display = "block";
        }
      } catch (error) {
        errorDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
        errorDiv.style.display = "block";
      }
    });
  }
});

// -------========------- Upload Profile Picture -------========-------
const uploadForm = document.getElementById("uploadProfilePicForm");
if (uploadForm) {
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(uploadForm);
    const response = await fetch('/upload-profile-picture', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.success) {
      alert("Profile picture updated!");
      location.reload();
    } else {
      alert("Failed to upload picture: " + data.error);
    }
  });
}

// -------========------- Delete Account Form -------========-------
const deleteAccountForm = document.getElementById("deleteAccountForm");
if (deleteAccountForm) {
  deleteAccountForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    const option = document.querySelector('input[name="deleteOption"]:checked')?.value;

    if (!option){alert("Please select an option to proceed."); return;}

    // Different popup based on option chosen
    if (option === 'anonymize') {
      message = "This action deletes your account and anonymizes all information associated with your account, including uploaded emails and comments.\n\nAre you sure you want to proceed? This action cannot be undone.";
    } else if (option === "delete") {
      message = "This deletes your account AND all information associated with it, including comments and uploaded emails.\n\nDeleting this removes information that could help other users identify phishing emails.\n\nAre you sure you want to proceed? This action cannot be undone.";
    }

    // Show right popup
    if (!confirm(message)) {
      return;
    }

    try {
      const response = await fetch("/delete-account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ option: option })
      });

      const data = await response.json();

      if (data.success) {
        alert("Your account has been deleted.");
        window.location.href = "/"; // redirect to homepage or login
      } else {
        alert("Failed to delete account: " + (data.message || "Unknown error"));
      }
      
    } catch (err) {
      console.error(err);
      alert("An error occurred while deleting your account.");
    }
  });
}

// -------========-------    Settings Panel Toggle Function    -------========-------
function toggleSettings() {
  const settingsPanel = document.getElementById('settingsPanel');
  const emailsSection = document.getElementById('emailsSection');

  if (!settingsPanel) return;

  if (settingsPanel.style.display === 'none' || settingsPanel.style.display === '') {
    // Show settings panel
    settingsPanel.style.display = 'block';

    // Hide uploaded emails
    if (emailsSection) emailsSection.style.display = 'none';
  } else {
    // Hide settings panel
    settingsPanel.style.display = 'none';

    // Show uploaded emails again
    if (emailsSection) emailsSection.style.display = 'block';
  }
}

// -------========-------    Forum Page    -------========-------
const MAX_COMMENT_LENGTH = 2000;

const newForum = document.getElementById("new-forum");
const Forum = document.getElementById("forum-main");
if (newForum) {
  newForum.addEventListener("click", Forum_Creator);
}

async function Forum_Creator(e) {
  try {
    e.preventDefault();
    const response = await fetch("/Forum_Creator", {
      method: "POST"
    });
    const data = await response.json();
    const page = document.body;

    page.insertAdjacentHTML("afterbegin", data.obj);
    document.getElementById("Close").addEventListener("click", DeletForumCreator);
    document.getElementById("SubmitForum").onsubmit = CreateForum;
    
  } catch (err) {
    console.error(err);
    alert("An error occurred while conecting to the back end.");
  }
}

let ForumPosts = document.getElementsByClassName("topic-item");
for (let i = 0; i < ForumPosts.length; i++) {
  ForumPosts[i].addEventListener("click", ShowForum);
}

function DeletForumCreator() {
  document.getElementById("CreateForumBackdrop").remove();
}

async function CreateForum(e) {
  e.preventDefault()
  try {
    let ForumData = new FormData(e.target);
    const response = await fetch("/Forum_Creation", {
      method: "POST",
      body: ForumData
    });

    const data = await response.json();

    DeletForumCreator();
    if (window.location.pathname === "/Forum") {
      location.reload();
    }

  } catch (err) {
    console.error(err);
    alert("An error occurred while connecting to the back end.");
  }
}


async function ShowForum(e) {
  e.preventDefault()

  document.querySelectorAll(".topic-item")
  .forEach(i => i.classList.remove("active"));

  this.classList.add("active");

  id = this.value;
  try {
    const response = await fetch("/Get_Forum", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ post_id: id })
    });

    const data = await response.json();
    
    const user = data["user"];
    const profilePicSrc = user.profile_picture 
      ? `data:image/png;base64,${user.profile_picture}` 
      : '/static/default_profile.png';
    
    const userInfoHTML = `
      <div class="discussion-user-info">
        <div class="user-avatar">
          <img src="${profilePicSrc}" alt="${user.username}'s avatar">
        </div>
        <div class="user-details">
          <span class="user-name">${user.username}</span>
          <span class="user-label">Author</span>
        </div>
      </div>
    `;
    
    const deleteButtonHTML = data.is_owner ? `
      <button class="delete-discussion-btn" data-discussion-id="${data.discussion_id}" title="Delete this discussion">
        <span class="delete-label">Delete</span>
        <i class="bi bi-trash"></i>
      </button>
    ` : '';

    const tag = data["Forum"][4];
    const tagHTML = tag
      ? `<div class="discussion-tag"><span class="badge bg-secondary">${tag}</span></div>`
      : "";

    Forum.children[0].innerHTML = `
      <div class="discussion-header">
        <div class="discussion-title-row">
          <div>
            <h2>${data["Forum"][0]}</h2>
            ${tagHTML}
          </div>
          <div class="discussion-right-group">
            ${userInfoHTML}
            ${deleteButtonHTML}
          </div>
        </div>
      </div>
      <div class="discussion-body">
        <p>` + data["Forum"][1] + `</p>
      </div>
      <div class="comments-section">
  <h3 class="comments-title">Comments</h3>

  <div id="comments-root"></div>

    ${data.is_logged_in ? `
      <div class="new-comment-box">
        <textarea
          id="new-comment-text"
          placeholder="Write a comment…"
          rows="3"
          maxlength="2000"
        ></textarea>

        <div class="comment-meta">
          <span id="char-counter">0 / 2000</span>
        </div>

        <button id="post-comment-btn">Comment</button>
      </div>
    ` : `
      <p class="login-hint">Log in to comment.</p>
    `}
</div>
    `;
await loadComments(id);


    const delBtn = Forum.querySelector(".delete-discussion-btn");
    if (delBtn) {
      delBtn.addEventListener("click", function (e) {
        e.preventDefault();
        const discussionId = this.getAttribute("data-discussion-id");
        openDeleteDiscussionModal(discussionId);
      });
    }

  } catch (err) {
    console.error(err);
    alert("An error occurred while conecting to the back end.");
  }
}

async function loadComments(discussionId) {
const res = await fetch(`/comments/${discussionId}`, {
  credentials: "same-origin"
});
  const data = await res.json();

  if (!data.success) {
    console.error("Failed to load comments");
    return;
  }

  const tree = buildCommentTree(data.comments);
  window.IS_LOGGED_IN = data.is_logged_in;

  document.getElementById("comments-root").innerHTML = `
    ${renderComments(tree)}
  `;
}

function renderComments(comments, depth = 0) {
  return comments.map(comment => `
    <div class="comment" style="margin-left: ${depth * 24}px">

      <img class="comment-avatar"
           src="/profile-picture/${comment.user.id}">

      <div class="comment-body">
        <div class="comment-header">
          <span class="comment-author">${comment.user.username}</span>
          <span class="comment-time">${comment.created_at}</span>
        </div>

        <p class="comment-text" data-id="${comment.id}">
          ${comment.text}
        </p>

        <textarea
          class="edit-textarea"
          data-id="${comment.id}"
          style="display: none;"
        >${comment.text}</textarea>


        <div class="comment-actions">
          ${window.IS_LOGGED_IN ? `
            <button class="reply-btn" data-id="${comment.id}">Reply</button>
          ` : ""}
          ${comment.is_owner ? `
            <button class="edit-comment-btn" data-id="${comment.id}">Edit</button>
            <button class="delete-comment-btn" data-id="${comment.id}">Delete</button>

            <button class="save-comment-btn" data-id="${comment.id}" style="display:none;">Save</button>
            <button class="cancel-edit-btn" data-id="${comment.id}" style="display:none;">Cancel</button>
          ` : ""}
        </div>

        <div class="reply-form-container"
             id="reply-form-${comment.id}"></div>

        ${comment.children?.length
          ? renderComments(comment.children, depth + 1)
          : ""}

        
      </div>
    </div>
  `).join("");
}

document.addEventListener("click", function (e) {
  if (!e.target.classList.contains("reply-btn")) return;

  const id = e.target.dataset.id;
  const container = document.getElementById(`reply-form-${id}`);

  if (container.innerHTML !== "") {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = `
    <form class="reply-form">
      <textarea
        placeholder="Write a reply..."
        maxlength="2000"
        required></textarea>
      <div class="comment-meta">
        <span class="reply-char-counter">0 / 2000</span>
      </div>

      <button type="submit">Reply</button>
    </form>
  `;
});

document.addEventListener("click", async function (e) {
  if (e.target.id !== "post-comment-btn") return;

  const textEl = document.getElementById("new-comment-text");
  if (!textEl) return;

  const text = textEl.value.trim();

  if (!text) return;

  if (text.length > MAX_COMMENT_LENGTH) {
    alert(`Your comment is too long. Maximum is ${MAX_COMMENT_LENGTH} characters.`);
    return;
  }

  const discussionId = document
    .querySelector(".topic-item.active")?.value;

  if (!discussionId) return;

  await fetch("/comment/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({
      discussion_id: discussionId,
      text: textEl.value,
      parent_id: null
    })
  });

  textEl.value = "";
  await loadComments(discussionId);
});

document.addEventListener("submit", async function (e) {
  if (!e.target.classList.contains("reply-form")) return;

  e.preventDefault();

  const textarea = e.target.querySelector("textarea");
  const text = textarea.value.trim();
  if (!text) return;

  if (text.length > MAX_COMMENT_LENGTH) {
    alert(`Reply is too long. Maximum is ${MAX_COMMENT_LENGTH} characters.`);
  return;
  }

  const parentId = e.target.closest(".comment")
    ?.querySelector(".reply-btn")?.dataset.id;

  const discussionId = document
    .querySelector(".topic-item.active")?.value;

  if (!discussionId || !parentId) return;

  await fetch("/comment/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({
      discussion_id: discussionId,
      parent_id: parentId,
      text
    })
  });

  textarea.value = "";
  await loadComments(discussionId);
});

document.addEventListener("click", async function (e) {
  if (!e.target.classList.contains("edit-comment-btn")) return;

  const commentEl = e.target.closest(".comment");
  if (!commentEl) return;

  // prevent multiple edit forms
  if (document.querySelector(".comment.editing")) return;

  commentEl.classList.add("editing");

  const textEl = commentEl.querySelector(".comment-text");
  const originalText = textEl.textContent;

  textEl.dataset.original = originalText;
  textEl.innerHTML = `
    <textarea
      class="edit-textarea"
      maxlength="${MAX_COMMENT_LENGTH}"
    >${originalText}</textarea>

    <div class="comment-meta">
      <span class="edit-char-counter">
        ${originalText.length} / ${MAX_COMMENT_LENGTH}
      </span>
    </div>

    <div class="edit-actions">
      <button class="save-edit-btn">Save</button>
      <button class="cancel-edit-btn">Cancel</button>
    </div>
  `;
});

document.addEventListener("click", function (e) {
  if (!e.target.classList.contains("cancel-edit-btn")) return;

  const commentEl = e.target.closest(".comment");
  if (!commentEl) return;

  const textEl = commentEl.querySelector(".comment-text");
  const originalText = textEl.dataset.original;
  textEl.innerHTML = originalText;
  delete textEl.dataset.original;
  commentEl.classList.remove("editing");
});

document.addEventListener("click", async function (e) {
  if (!e.target.classList.contains("save-edit-btn")) return;

  const commentEl = e.target.closest(".comment");
  if (!commentEl) return;

  const textarea = commentEl.querySelector(".edit-textarea");
  if (!textarea) return;

  const newText = textarea.value.trim();
  if (!newText) return;
  if (newText.length > MAX_COMMENT_LENGTH) {
  alert(`Edited comment is too long. Maximum is ${MAX_COMMENT_LENGTH} characters.`);
  return;
  }

  const commentId = commentEl.querySelector(".edit-comment-btn")?.dataset.id;
  if (!commentId) return;

  const res = await fetch("/comment/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({
      comment_id: commentId,
      text: newText
    })
  });

  const data = await res.json();
  if (!data.success) {
    alert("Failed to edit comment");
    return;
  }

  // reload comments to stay in sync with DB
  const discussionId = document
    .querySelector(".topic-item.active")?.value;

  if (discussionId) {
    await loadComments(discussionId);
  }
});

document.addEventListener("click", async function (e) {
  if (!e.target.classList.contains("delete-comment-btn")) return;

  const commentId = e.target.dataset.id;
  if (!commentId) return;

  const confirmDelete = confirm(
    "Are you sure you want to delete this comment?"
  );
  if (!confirmDelete) return;

  const res = await fetch("/comment/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ comment_id: commentId })
  });

  const data = await res.json();
  if (!data.success) {
    alert("Failed to delete comment");
    return;
  }

  const discussionId = document
    .querySelector(".topic-item.active")?.value;

  if (discussionId) {
    await loadComments(discussionId);
  }
});


function buildCommentTree(flatComments) {
  const map = {};
  const roots = [];

  flatComments.forEach(c => {
    c.children = [];
    map[c.id] = c;
  });

  flatComments.forEach(c => {
    if (c.parent_id) {
      map[c.parent_id]?.children.push(c);
    } else {
      roots.push(c);
    }
  });

  return roots;
}

document.addEventListener("input", function (e) {
  if (e.target.id !== "new-comment-text") return;

  const counter = document.getElementById("char-counter");
  if (!counter) return;

  const len = e.target.value.length;
  counter.textContent = `${len} / 2000`;

  if (len > 2000) {
    counter.classList.add("over-limit");
  } else {
    counter.classList.remove("over-limit");
  }
});

document.addEventListener("input", function (e) {
  if (!e.target.closest(".reply-form")) return;

  const counter = e.target
    .closest(".reply-form")
    ?.querySelector(".reply-char-counter");

  if (!counter) return;

  const len = e.target.value.length;
  counter.textContent = `${len} / ${MAX_COMMENT_LENGTH}`;

  if (len > MAX_COMMENT_LENGTH) {
    counter.classList.add("over-limit");
  } else {
    counter.classList.remove("over-limit");
  }
});

document.addEventListener("input", function (e) {
  if (!e.target.classList.contains("edit-textarea")) return;

  const counter = e.target
    .closest(".comment-text")
    ?.querySelector(".edit-char-counter");

  if (!counter) return;

  const len = e.target.value.length;
  counter.textContent = `${len} / ${MAX_COMMENT_LENGTH}`;

  if (len > MAX_COMMENT_LENGTH) {
    counter.classList.add("over-limit");
  } else {
    counter.classList.remove("over-limit");
  }
});

// -------========-------    Delete Discussion Modal Functions    -------========-------
let pendingDeleteDiscussionId = null;

function openDeleteDiscussionModal(discussionId) {
  const modal = document.getElementById("DeleteDiscussionModal");
  pendingDeleteDiscussionId = discussionId;
  modal.style.display = "flex";
}

function closeDeleteDiscussionModal() {
  const modal = document.getElementById("DeleteDiscussionModal");
  modal.style.display = "none";
  pendingDeleteDiscussionId = null;
}

document.addEventListener("DOMContentLoaded", function () {

  const deleteDiscussionModal = document.getElementById("DeleteDiscussionModal");

  if (deleteDiscussionModal) {
    deleteDiscussionModal.addEventListener("click", function (event) {
      if (event.target === deleteDiscussionModal) {
        closeDeleteDiscussionModal();
      }
    });

    const confirmDeleteDiscussionBtn = document.getElementById("confirmDeleteDiscussionBtn");

    if (confirmDeleteDiscussionBtn) {
      confirmDeleteDiscussionBtn.addEventListener("click", async function () {
        if (!pendingDeleteDiscussionId) return;

        confirmDeleteDiscussionBtn.disabled = true;
        confirmDeleteDiscussionBtn.textContent = "Deleting...";

        try {
          const id = encodeURIComponent(pendingDeleteDiscussionId);
          const resp = await fetch(`/Delete_Discussion/${id}`, {
            method: "DELETE",
            credentials: "same-origin"
          });

          let body;
          try {
            body = await resp.json();
          } catch (err) {
            console.error("Failed to parse delete response JSON", err);
            alert("Failed to parse server response. See console for details.");
            return;
          }

          if (resp.ok && body.success) {
            closeDeleteDiscussionModal();
            location.reload();
          } else {
            if (resp.status === 401) {
              alert("You must be logged in to delete this discussion. Please log in and try again.");
            } else if (resp.status === 404) {
              alert("Discussion not found or you do not have permission to delete it.");
            } else {
              alert("Failed to delete discussion: " + (body.error || body.message || `status ${resp.status}`));
            }
          }

        } catch (err) {
          console.error("Delete discussion fetch error:", err);
          alert("Network or server error while deleting discussion. See console for details.");
        } finally {
          confirmDeleteDiscussionBtn.disabled = false;
          confirmDeleteDiscussionBtn.textContent = "Delete Discussion";
        }
      });
    }
  }

  const deleteButtons = document.querySelectorAll(".delete-discussion-btn");
  deleteButtons.forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const discussionId = this.getAttribute("data-discussion-id");
      openDeleteDiscussionModal(discussionId);
    });
  });

});

// -------========-------    Reanalyze Modal Functions    -------========-------
let pendingReanalyzeId = null;

function openReanalyzeModal(emailId) {
  const modal = document.getElementById("ReanalyzeModal");
  pendingReanalyzeId = emailId;
  modal.style.display = "flex";
}

function closeReanalyzeModal() {
  const modal = document.getElementById("ReanalyzeModal");
  modal.style.display = "none";
  pendingReanalyzeId = null;
}

// -------========-------    Delete Email Modal Functions    -------========-------
let pendingDeleteEmailId = null;

function openDeleteEmailModal(emailId) {
  const modal = document.getElementById("DeleteEmailModal");
  pendingDeleteEmailId = emailId;
  modal.style.display = "flex";
}

function closeDeleteEmailModal() {
  const modal = document.getElementById("DeleteEmailModal");
  modal.style.display = "none";
  pendingDeleteEmailId = null;
}

document.addEventListener("DOMContentLoaded", function() {

  const reanalyzeModal = document.getElementById("ReanalyzeModal");
  if (reanalyzeModal) {
    reanalyzeModal.addEventListener("click", function(event) {
      if (event.target === reanalyzeModal) {
        closeReanalyzeModal();
      }
    });

    const confirmReanalyzeBtn = document.getElementById("confirmReanalyzeBtn");
    if (confirmReanalyzeBtn) {
      confirmReanalyzeBtn.addEventListener("click", async function() {
        if (!pendingReanalyzeId) return;

        confirmReanalyzeBtn.disabled = true;

        const useAICheckbox = document.getElementById("reanalyzeUseAI");
        const useAI = useAICheckbox ? !!useAICheckbox.checked : false;

        try {
          // Fetch email payload from API (keeps auth/ownership checks server-side)
          const id = encodeURIComponent(pendingReanalyzeId);
          const resp = await fetch(`/api/email/${id}`, { method: 'GET', credentials: 'same-origin' });

          // Handle HTTP errors
          if (!resp.ok) {
            if (resp.status === 401) {
              alert('You must be logged in to re-analyze this email. Please log in and try again.');
            } else if (resp.status === 404) {
              alert('Email not found or you do not have permission to access it.');
            } else {
              const txt = await resp.text().catch(()=>null);
              alert('Failed to load email for re-analysis: ' + (txt || `status ${resp.status}`));
            }
            return;
          }

          let body;
          try {
            body = await resp.json();
          } catch (err) {
            console.error('Failed to parse /api/email JSON', err);
            alert('Failed to parse server response. See console for details.');
            return;
          }

          if (!body || !body.success || !body.email) {
            console.error('Unexpected /api/email response:', body);
            alert('Server returned unexpected data for the email. See console for details.');
            return;
          }

          // Store the same payload the index page expects
          const payload = {
            email: body.email,
            useAI: useAI
          };
          localStorage.setItem('reanalyze_payload', JSON.stringify(payload));

          // Navigate to index analysis section (the index script will consume the payload and start analysis)
          window.location.href = '/#analysis';

        } catch (err) {
          console.error("Reanalyze fetch error:", err);
          alert("Network or server error while requesting re-analysis. See console for details.");
        } finally {
          confirmReanalyzeBtn.disabled = false;
          // pendingReanalyzeId cleared on modal close or navigation
        }
      });
    }
  }

  const reanalyzeButtons = document.querySelectorAll(".reanalyze-btn");
  reanalyzeButtons.forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.preventDefault();
      const emailId = this.getAttribute("data-id");
      openReanalyzeModal(emailId);
    });
  });

  // -------========-------    Delete Email Modal Event Listeners    -------========-------
  const deleteEmailModal = document.getElementById("DeleteEmailModal");
  if (deleteEmailModal) {
    // Close modal when clicking outside
    deleteEmailModal.addEventListener("click", function(event) {
      if (event.target === deleteEmailModal) {
        closeDeleteEmailModal();
      }
    });

    // Handle confirm delete button
    const confirmDeleteEmailBtn = document.getElementById("confirmDeleteEmailBtn");
    if (confirmDeleteEmailBtn) {
      confirmDeleteEmailBtn.addEventListener("click", async function() {
        if (!pendingDeleteEmailId) return;

        confirmDeleteEmailBtn.disabled = true;
        confirmDeleteEmailBtn.textContent = "Deleting...";

        try {
          const id = encodeURIComponent(pendingDeleteEmailId);
          const resp = await fetch(`/api/email/${id}`, { 
            method: 'DELETE', 
            credentials: 'same-origin' 
          });

          let body;
          try {
            body = await resp.json();
          } catch (err) {
            console.error('Failed to parse delete response JSON', err);
            alert('Failed to parse server response. See console for details.');
            return;
          }

          if (resp.ok && body.success) {
            const row = document.querySelector(`button.delete-btn[data-id="${pendingDeleteEmailId}"]`)?.closest('tr');
            if (row) {
              row.remove();
            }
            closeDeleteEmailModal();
          } else {
            if (resp.status === 401) {
              alert('You must be logged in to delete this email. Please log in and try again.');
            } else if (resp.status === 404) {
              alert('Email not found or you do not have permission to delete it.');
            } else {
              alert('Failed to delete email: ' + (body.error || body.message || `status ${resp.status}`));
            }
          }
        } catch (err) {
          console.error("Delete email fetch error:", err);
          alert("Network or server error while deleting email. See console for details.");
        } finally {
          confirmDeleteEmailBtn.disabled = false;
          confirmDeleteEmailBtn.textContent = "Delete Email";
        }
      });
    }
  }

  // Attach click handlers to all delete buttons
  const deleteButtons = document.querySelectorAll(".delete-btn");
  deleteButtons.forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.preventDefault();
      const emailId = this.getAttribute("data-id");
      openDeleteEmailModal(emailId);
    });
  });

  // -------========-------    reanalyze_payload handling -------========-------
  try {
    const raw = localStorage.getItem('reanalyze_payload');
    if (raw) {
      let payload = null;
      try {
        payload = JSON.parse(raw);
      } catch (e) {
        console.error("Invalid reanalyze_payload JSON:", e);
        localStorage.removeItem('reanalyze_payload');
      }

      if (payload && payload.email) {
        // Remove key immediately to avoid repeated runs
        localStorage.removeItem('reanalyze_payload');

        // Use same client-side analysis flow as upload - set AI pref and uploadedFiles
        window.useAI = !!payload.useAI;
        window.uploadedFiles = [payload.email];
        window.currentFileIndex = 0;
        window.fileAnalysisResults = {};

        // Ensure analysis view is visible (toggleAnalysis is resilient on pages without UpForm)
        toggleAnalysis();
        hideSidebars();

        const downloadSection = document.getElementById("downloadSection");
        if (downloadSection) downloadSection.classList.add("hidden");

        // Start analysis for the single email
        renderFileAnalysis(0);
        runFileAnalyses(0);
      }
    }
  } catch (e) {
    console.error("Error handling reanalyze_payload:", e);
  }
});

// Download Logic
document.addEventListener("DOMContentLoaded", () => {
    const emailsBtn = document.getElementById("downloadEmails");
    const analysisBtn = document.getElementById("downloadAnalysis");
    const bothBtn = document.getElementById("downloadBoth");

    const modalElement = document.getElementById("downloadErrorModal");
    const msgBox = document.getElementById("downloadErrorMessage");
    const modal = modalElement ? new bootstrap.Modal(modalElement) : null;

    async function check(route) {
        const res = await fetch("/check/" + route);
        return res.json();
    }

    function showMessage(msg) {
        if (msgBox && modal) {
            msgBox.innerHTML = `<p>${msg}</p>`;
            modal.show();
        } else {
            alert(msg); // fallback
        }
    }

    if (emailsBtn) {
        emailsBtn.addEventListener("click", async () => {
            const data = await check("emails");
            if (!data.hasEmails) return showMessage("You have no emails to download.");
            window.location.href = "/download/emails";
        });
    }

    if (analysisBtn) {
        analysisBtn.addEventListener("click", async () => {
            const data = await check("analysis");
            if (!data.hasAnalysis) return showMessage("You have no analyses to download.");
            window.location.href = "/download/analysis";
        });
    }

    if (bothBtn) {
        bothBtn.addEventListener("click", async () => {
            const data = await check("both");
            if (!data.hasEmails && !data.hasAnalysis) return showMessage("No emails or analyses to download.");
            if (!data.hasEmails) return showMessage("No emails to download.");
            if (!data.hasAnalysis) return showMessage("No analyses to download.");
            window.location.href = "/download/both";
        });
  }
});
