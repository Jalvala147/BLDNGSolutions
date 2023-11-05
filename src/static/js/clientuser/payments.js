const orderSelect = document.getElementById('order-select');
const selectedOrderInfo = document.getElementById('selected-order-info');
orderSelect.addEventListener('change', function () {
    const selectedOption = orderSelect.options[orderSelect.selectedIndex];
    const orderInfoText = selectedOption.text;
    selectedOrderInfo.textContent = `Información de la orden seleccionada: ${orderInfoText}`;
});

function mostrarFormulario(tipoPago) {
    var formularios = document.getElementsByClassName('formulario');
    for (var i = 0; i < formularios.length; i++) {
        formularios[i].style.display = 'none';
    }

    var formularioSeleccionado = document.getElementById(tipoPago);
    formularioSeleccionado.style.display = 'block';
}




function generarOrdenPago() {
    // Recopila los valores de los campos del formulario
    var bancoDestino = document.getElementById("banco_destino").value;
    var numeroCuenta = document.getElementById("numero_cuenta").value;
    var nombreTitular = document.getElementById("nombre_titular").value;
    var monto = document.getElementById("monto").value;
    var concepto = document.getElementById("concepto").value;

    // Actualiza el campo oculto con la información necesaria para el PDF
    var pdfInfo = `Banco de destino: ${bancoDestino}, Número de cuenta: ${numeroCuenta}, Nombre del titular: ${nombreTitular}, Monto: ${monto}, Concepto: ${concepto}`;
    document.getElementById("pdf_info").value = pdfInfo;

    // Envía el formulario para generar el PDF
    document.querySelector('form').submit();
}


function actualizarCamposPago() {
    var select = document.getElementById("order-select");
    var selectedOption = select.options[select.selectedIndex];
    var montoInput = document.getElementById("monto");
    var conceptoInput = document.getElementById("concepto");

    if (selectedOption) {
        var monto = selectedOption.getAttribute("data-amount");
        var concepto = "Pago de Orden #" + selectedOption.value;

        montoInput.value = "$" + monto;
        conceptoInput.value = concepto;
    }
}


const tipoPagoSelect = document.getElementById('tipo_pago');

// Initially, disable the payment method select
tipoPagoSelect.setAttribute('disabled', 'disabled');

orderSelect.addEventListener('change', function () {
    const selectedOption = orderSelect.options[orderSelect.selectedIndex];
    if (selectedOption.value) {
        // Enable the select of payment methods when an order is selected
        tipoPagoSelect.removeAttribute('disabled');
    } else {
        // Disable the select of payment methods if no order is selected
        tipoPagoSelect.setAttribute('disabled', 'disabled');
    }
});


