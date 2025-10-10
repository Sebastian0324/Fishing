let login = document.getElementById("Login");

document.getElementById("Login_btn").addEventListener("click", function() {
  login.style.display = "block";
});
document.getElementById("Close_Login").addEventListener("click", function() {
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


// -------========-------    Front Page    -------========-------
let UpForm = document.getElementById("uploadForm");
if (UpForm != null) {
  UpForm.onsubmit = async (e) => {
    e.preventDefault();

    let formData = new FormData(e.target);
    let response = await fetch("/upload", { method: "POST", body: formData });
    let data = await response.json();
    
    document.getElementById("result").innerHTML =
      `<b>${data.subject}</b><br>From: ${data.from}<br>${data.preview}`;
  };
}

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
