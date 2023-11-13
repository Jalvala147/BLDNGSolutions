document.addEventListener("DOMContentLoaded", function () {
    const noteColumns = document.querySelectorAll(".note-column");

    noteColumns.forEach(function (column) {
        const userNote = column.querySelector(".user-note");
        const notaInput = column.querySelector(".nota-input");
        const confirmBtn = column.querySelector(".confirm-btn");

        column.addEventListener("click", function (event) {
            if (event.target.classList.contains("nota")) {
                userNote.style.display = "none";
                notaInput.style.display = "block";
                confirmBtn.style.display = "block";
            }
        });

        document.addEventListener("click", function (event) {
            if (!column.contains(event.target)) {
                userNote.style.display = "block";
                notaInput.style.display = "none";
                confirmBtn.style.display = "none";
            }
        });

        confirmBtn.addEventListener("click", function () {
            userNote.textContent = notaInput.value;
            userNote.style.display = "block";
            notaInput.style.display = "none";
            confirmBtn.style.display = "none";
        });
    });
})