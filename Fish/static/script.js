document.getElementById("uploadForm").onsubmit = async (e) => {
  e.preventDefault();

  let formData = new FormData(e.target);
  let response = await fetch("/upload", { method: "POST", body: formData });
  let data = await response.json();
  
  document.getElementById("result").innerHTML =
    `<b>${data.subject}</b><br>From: ${data.from}<br>${data.preview}`;
};

let form = document.getElementById("Login");
document.getElementById("Login_btn").addEventListener("click", function() {
  form.style.display = "block";
  console.log("Block");
});
document.getElementById("Close_Login").addEventListener("click", function() {
  form.style.display = "None";
});