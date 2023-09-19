document.addEventListener("DOMContentLoaded", function () {
    const containers = document.querySelectorAll(".container");
  
    containers.forEach((container) => {
      const circles = container.querySelectorAll(".circle");
      const progressBar = container.querySelector(".progress-bar .indicator");
  
      let activeCircleIndex = 0;
  
      // encuentra el indice del ultimo circulo active
      circles.forEach((circle, index) => {
        if (circle.classList.contains("active")) {
          activeCircleIndex = index;
        }
      });
  
      // calcular el ancho 
      const progressBarWidth = (activeCircleIndex / (circles.length - 1)) * 100;
  
      progressBar.style.width = progressBarWidth + "%";
    });
  });
  