fetch("/api/status")
  .then(response => response.json())
  .then(status => { document.querySelector("#status").textContent = `Checkout ${status.version}`; });
