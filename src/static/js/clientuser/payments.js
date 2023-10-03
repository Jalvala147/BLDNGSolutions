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
    var bancoDestino = document.getElementById('banco_destino').value;
    var numeroCuenta = document.getElementById('numero_cuenta').value;

    document.getElementById('info_banco').innerText = bancoDestino;
    document.getElementById('info_cuenta').innerText = numeroCuenta;

    document.getElementById('orden_pago').style.display = 'block';
}


