let login = document.getElementById("Login");

document.getElementById("Login_btn").addEventListener("click", function() {
  login.style.display = "block";
});
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
    
    // Handle success response
    if (data.success && data.data) {
      document.getElementById("result").innerHTML = `
        <div class="alert alert-success" role="alert">
          <h5>✓ Email Analysis Complete - ID: ${data.email_id}</h5>
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
