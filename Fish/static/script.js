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
    
    document.getElementById("result").innerHTML =
      `<b>${data.subject}</b><br>From: ${data.from}<br>${data.preview}`;
  };
}
