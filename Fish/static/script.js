let login = document.getElementById("Login");

document.getElementById("Login_btn").addEventListener("click", function() {
  login.style.display = "block";
});
document.getElementById("Close_Login").addEventListener("click", function() {
  document.getElementById("Login").style.display = "None";
});

let SignIn = document.getElementById("SignIn");
let SignUp = document.getElementById("SignUp");
document.getElementById("SignIn/Up").addEventListener("click", function() {
    SignIn.classList.toggle("hidden");
    SignUp.classList.toggle("hidden");
});


// -------========-------    Front Page    -------========-------
let UpForm = document.getElementById("uploadForm");
if (UpForm != null) {
  UpForm.onsubmit = async (e) => {
    e.preventDefault();

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
            <h6 class="card-subtitle mb-2 text-muted">Body Preview</h6>
            <p class="card-text">${data.data.body_preview || 'No content'}</p>
            <hr>
            <h6 class="card-subtitle mb-2 text-muted">Extracted URLs (${data.data.urls_count || 0})</h6>
            ${urlsList}
          </div>
        </div>
      `;
    }
  };
}
