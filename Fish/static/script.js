
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
}
// -------========-------    Front Page    -------========-------
// -------========-------    Upload Page    -------========-------  
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



    // Show analysis section and hide sidebars
    toggleAnalysis();
    hideSidebars();
    
    // Show loading spinner
    const loadingSpinner = document.getElementById("loadingSpinner");
    const downloadSection = document.getElementById("downloadSection");
    if (loadingSpinner) loadingSpinner.style.display = "block";
    if (downloadSection) downloadSection.classList.add("hidden");

    let formData = new FormData(e.target);
    let respons = await fetch("/upload", { method: "POST", body: formData });
    let data = await respons.json();
    
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
  const bodyText = data.data.body_text?.trim() || 'No content';
  const downloadSection = document.getElementById("downloadSection");

  // Insert the updated HTML with progress bars and sections
  document.getElementById("result").innerHTML = `
    <div class="row">
      <div class="col-md-8">
        <div class="alert alert-success" role="alert">
          <h5>✓ Email Analysis Complete - ID: ${data.email_id}</h5>
        </div>

        <div id="virusSection" class="mt-4">
          <div class="card">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
              <div class="text-center my-3">
                <div class="spinner-border text-info" role="status">
                  <span class="visually-hidden">Loading VirusTotal response...</span>
                </div>
                <p class="mt-2 text-muted">Checking with VirusTotal...</p>
              </div>
            </div>
          </div>
        </div>

       <div id="ipSection" class="mt-4"></div>

        <div id="llmSection" class="mt-4">
          <div class="card">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">LLM Analysis</h6>
              <div class="text-center my-3">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Loading LLM response...</span>
                </div>
                <p class="mt-2 text-muted">Analyzing with AI...</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card h-100">
          <div class="card-body">
            <h6 class="card-subtitle mb-3 text-muted">Analysis Progress</h6>

            ${["vt", "abuse", "llm"].map(id => `
              <div id="${id}ProgressContainer" class="mb-4">
                <div class="mb-2 text-muted small">${id === "vt" ? "VirusTotal" : id === "abuse" ? "AbuseIPDb" : "LLM"} analysis progress</div>
                <div class="progress" style="height: 1.25rem;">
                  <div id="${id}ProgressBar" class="progress-bar progress-bar-striped progress-bar-animated ${id === "vt" ? "bg-info" : id === "abuse" ? "bg-warning" : "bg-primary"}" 
                       role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                </div>
              </div>
            `).join("")}

          </div>
        </div>
      </div>
    </div>
  `;




  // Helper function to update progress bar
  function updateProgress(barId, status, percentage = null) {
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

  // Launch all API calls in parallel and sync progress bars to actual completion
  const senderIp = data.data.sender_ip || "";
  
  // Track completion of all analyses
  let completedCount = 0;
  const totalAnalyses = 3;
  
  function checkAllCompleted() {
    completedCount++;
    if (completedCount >= totalAnalyses) {
      // Show download button after all analyses complete
      if (downloadSection) downloadSection.classList.remove("hidden");
    }
  }
  
  // VirusTotal API call with progress tracking
  if (data.email_id) {
    updateProgress("vtProgressBar", "start");
    callVirusTotalAPI(data.email_id).then(() => {
      updateProgress("vtProgressBar", "complete");
      checkAllCompleted();
    }).catch(() => {
      updateProgress("vtProgressBar", "error");
      checkAllCompleted();
    });
  } else {
    updateProgress("vtProgressBar", "error");
    checkAllCompleted();
  }
  
  // AbuseIPDB API call with progress tracking
  if (senderIp) {
    updateProgress("abuseProgressBar", "start");
    callAbuseIPAPI(senderIp).then(() => {
      updateProgress("abuseProgressBar", "complete");
      checkAllCompleted();
    }).catch(() => {
      updateProgress("abuseProgressBar", "error");
      checkAllCompleted();
    });
  } else {
    updateProgress("abuseProgressBar", "error");
    checkAllCompleted();
  }
  
  // LLM API call with progress tracking
  if (bodyText) {
    updateProgress("llmProgressBar", "start");
    callLLMAPI(bodyText, data.email_id).then(() => {
      updateProgress("llmProgressBar", "complete");
      checkAllCompleted();
    }).catch(() => {
      updateProgress("llmProgressBar", "error");
      checkAllCompleted();
    });
  } else {
    updateProgress("llmProgressBar", "error");
    checkAllCompleted();
  }
    }
  };
}

// -------========-------    LLM API Call Function    -------========-------
async function callLLMAPI(bodyText, emailId) {
  const llmSection = document.getElementById("llmSection");
  
  if (!llmSection) return;
  
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
      body: JSON.stringify({ message: bodyText })
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
              <h6>🔍 Phishing Analysis Results</h6>
              <hr>
              <div style="white-space: pre-wrap;">${llmData.response}</div>
            </div>
          </div>
        </div>
      `;
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
  }
}

// -------========-------    AbuseIPDB API Call Function    -------========-------
async function callAbuseIPAPI(ipAddress) {
  const ipSection = document.getElementById("ipSection");
  
  if (!ipSection) return;
  
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
      let riskIcon = "✓";
      
      if (ipData.abuse_score >= 75) {
        riskLevel = "High";
        riskClass = "danger";
        riskIcon = "⚠";
      } else if (ipData.abuse_score >= 50) {
        riskLevel = "Medium";
        riskClass = "warning";
        riskIcon = "⚡";
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
              ${ipData.is_malicious ? '<p class="mb-0 mt-2"><strong>⚠ Warning:</strong> This IP has been reported for malicious activity.</p>' : ''}
            </div>
          </div>
        </div>
      `;
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
  }
}

// -------========-------    VirusTotal API Call Function    -------========-------
async function callVirusTotalAPI(emailId) {
  const virusSection = document.getElementById("virusSection");
  
  if (!virusSection) return;
  
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
      let threatIcon = "🛡️";
      
      if (malicious > 0) {
        threatLevel = "Malicious";
        threatClass = "danger";
        threatIcon = "🚨";
      } else if (suspicious > 0) {
        threatLevel = "Suspicious";
        threatClass = "warning";
        threatIcon = "⚠️";
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
              ${reportData.is_malicious ? '<p class="mb-0 mt-2"><strong>🚨 Warning:</strong> This file has been flagged as malicious by antivirus engines.</p>' : ''}
              ${reportData.file_hash ? `<p class="mb-0 mt-2"><small><strong>File Hash:</strong> <code>${reportData.file_hash.substring(0, 16)}...</code></small></p>` : ''}
            </div>
          </div>
        </div>
      `;
    } else if (reportData.status_code === 404) {
      // File not yet in VirusTotal database - show info message
      virusSection.innerHTML = `
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">VirusTotal Analysis</h6>
            <div class="alert alert-info mb-0">
              <h6>🔍 VirusTotal Scan</h6>
              <hr>
              <p class="mb-0">File has been submitted to VirusTotal for analysis. Results will be available in a few minutes.</p>
              <p class="mb-0 mt-2"><small>You can check the results later using the file report API.</small></p>
            </div>
          </div>
        </div>
      `;
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
  }
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
      leftIcon.textContent = '◀';
    } else {
      // Collapse left sidebar
      leftSidebar.classList.add('collapsed');
      layout.classList.add('left-collapsed');
      leftIcon.textContent = '▶';
    }
  } else if (side === 'right') {
    if (rightSidebar.classList.contains('collapsed')) {
      // Expand right sidebar
      rightSidebar.classList.remove('collapsed');
      layout.classList.remove('right-collapsed');
      rightIcon.textContent = '▶';
    } else {
      // Collapse right sidebar
      rightSidebar.classList.add('collapsed');
      layout.classList.add('right-collapsed');
      rightIcon.textContent = '◀';
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
    leftIcon.textContent = '▶';
  }
  
  if (rightSidebar && !rightSidebar.classList.contains('collapsed')) {
    rightSidebar.classList.add('collapsed');
    layout.classList.add('right-collapsed');
    rightIcon.textContent = '◀';
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
