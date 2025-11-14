export function ready() {
  var links = document.querySelectorAll(".page__toc a");
  links.forEach(link => {
    link.addEventListener("click", function (event) {
      const pop = event.target.closest(".page__toc");
      if (pop) { pop.hidePopover(); }
    });
  });
}
