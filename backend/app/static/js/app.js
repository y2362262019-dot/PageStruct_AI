document.body.addEventListener("htmx:responseError", function () {
  console.error("HTMX request failed.");
});
