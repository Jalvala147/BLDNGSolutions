// Carrito 
let cartIcon = document.querySelector("#cart-icon");
let cart = document.querySelector(".cart");
let closeCart = document.querySelector("#close-cart");

//Abrir carrito
cartIcon.onclick = () => {
    cart.classList.add("active"); // Agrega la clase "active" al elemento con la clase "cart"
};

//Cerrar carrito
closeCart.onclick = () => {
    cart.classList.remove("active"); // Elimina la clase "active" del elemento con la clase "cart"
};

// Carrito con js
if (document.readyState == "loading") {
    document.addEventListener("DOMContentLoaded", ready);
} else {
    ready();
}

//Función para inicializar el carrito
function ready() {
    //Remove items from cart
    var removeCartButtons = document.getElementsByClassName("cart-remove");
    for (var i = 0; i < removeCartButtons.length; i++) {
        var button = removeCartButtons[i];
        button.addEventListener("click", removeCartItem);
    }
    //Cambios de cantidad
    var quantityInputs = document.getElementsByClassName("cart-quantity");
    for (var i = 0; i < quantityInputs.length; i++) {
        var input = quantityInputs[i];
        input.addEventListener("change", quantityChanged);
    }
    //Agregar al carrito 
    var addCart = document.getElementsByClassName("add-cart");
    for (var i = 0; i < addCart.length; i++) {
        var button = addCart[i];
        button.addEventListener("click", addCartClicked);
    }
    //Boton de pedir
    document
        .getElementsByClassName("btn-buy")[0]
        .addEventListener("click", buyButtonClicked);
}

//boton de pedir
function buyButtonClicked() {
    var cartContent = document.getElementsByClassName("cart-content")[0];
    if (cartContent.children.length === 0) {
        alert('No hay elementos en el carrito. Agrega productos antes de pedir.');
    } else {
        alert('Pedido realizado con éxito');
        while (cartContent.hasChildNodes()) {
            cartContent.removeChild(cartContent.firstChild);
        }
        updateTotal();
    }
}


//Función para remover un item del carrito
function removeCartItem(event) {
    var buttonClicked = event.target;
    var cartItem = buttonClicked.parentElement;
    var machineId = cartItem.getElementsByClassName("cart-machine-id")[0].value; // Obtener el ID de la máquina

    // Eliminar visualmente el elemento del carrito
    cartItem.remove();

    // Eliminar el ID de la máquina de la lista de IDs en el formulario
    var cartMachineIdsField = document.getElementById("cart-machine-ids");
    var cartMachineIds = cartMachineIdsField.value.split(","); // Convertir la cadena en una lista
    var updatedCartMachineIds = cartMachineIds.filter(id => id !== machineId); // Filtrar los IDs para eliminar el que se borró
    cartMachineIdsField.value = updatedCartMachineIds.join(","); // Convertir la lista en una cadena separada por comas

    updateTotal();
}




//Función para cambios de cantidad
function quantityChanged(event) {
    var input = event.target;
    if (isNaN(input.value) || input.value <= 0) {
        input.value = 1;
    }
    updateTotal();
}

//Función para agregar al carrito
function addCartClicked(event) {
    var button = event.target;
    var shopProducts = button.parentElement;
    var title = shopProducts.getElementsByClassName("product-title")[0].innerText;
    var price = shopProducts.getElementsByClassName("price")[0].innerText;
    var productImg = shopProducts.getElementsByClassName("product-img")[0].src;
    var machineId = shopProducts.getElementsByClassName("machine-id")[0].innerText; // Cambio aquí

    // Verificar si el producto ya está en el carrito
    var cartItemsNames = document.getElementsByClassName("cart-product-title");
    for (var i = 0; i < cartItemsNames.length; i++) {
        if (cartItemsNames[i].innerText === title) {
            alert("Ya has agregado esta máquina");
            return; // Salir de la función si el producto está duplicado
        }
    }

    // Si el producto no está duplicado, agregarlo al carrito
    addProductToCart(title, price, productImg, machineId);
    updateTotal();

    // Mostrar mensaje flash
    var flashMessage = document.getElementById("flashMessage");
    flashMessage.style.display = "block";
    setTimeout(function () {
        flashMessage.style.display = "none";
    }, 1400); // Ocultar el mensaje después de 1.4 segundos

    // Obtener los IDs de las máquinas en el carrito
    var cartMachineIds = [];
    var cartItems = document.getElementsByClassName("cart-box");
    for (var i = 0; i < cartItems.length; i++) {
        var cartMachineId = cartItems[i].getElementsByClassName("cart-machine-id")[0].value;
        cartMachineIds.push(cartMachineId);
    }

    // Establecer los IDs de las máquinas en el campo oculto del formulario
    var cartMachineIdsField = document.getElementById("cart-machine-ids");
    cartMachineIdsField.value = cartMachineIds.join(","); // Convertir la lista en una cadena separada por comas
}


//Función para agregar un producto al carrito
function addProductToCart(title, price, productImg, machineId) {
    var cartShopBox = document.createElement("div");
    cartShopBox.classList.add("cart-box");
    var cartItems = document.getElementsByClassName("cart-content")[0];
    var cartItemsNames = cartItems.getElementsByClassName("cart-product-title");
    for (var i = 0; i < cartItemsNames.length; i++) {
        if (cartItemsNames[i].innerText === title) {
            alert("Ya has agregado esta máquina");
            return;
        }
    }

    var cartBoxContent = `
        <img src="${productImg}" alt="" class="cart-img">
        <!-- Contenido de la caja -->
        <input type="hidden" class="cart-machine-id" value="${machineId}">
        <div class="detail-box">
            <div class="cart-product-title">${title}</div>
            <div class="cart-product-id">ID: ${machineId}</div> 
            <div class="cart-price">${price}</div>
            <input type="number" value="1" min="1" max="4" class="cart-quantity" >
            <span>semanas</span>
        </div>
        <!--borrar carrito-->
        <i class="bx bxs-trash-alt cart-remove"></i>`;
    cartShopBox.innerHTML = cartBoxContent;
    cartItems.appendChild(cartShopBox);
    cartShopBox.getElementsByClassName("cart-remove")[0].addEventListener("click", removeCartItem);
    cartShopBox.getElementsByClassName("cart-quantity")[0].addEventListener("change", quantityChanged);
}




//Función para actualizar el total del carrito
function updateTotal() {
    var cartContent = document.getElementsByClassName("cart-content")[0];
    var cartBoxes = cartContent.getElementsByClassName("cart-box");
    var total = 0;
    for (var i = 0; i < cartBoxes.length; i++) {
        var cartBox = cartBoxes[i];
        var priceElement = cartBox.getElementsByClassName("cart-price")[0];
        var quantityElement = cartBox.getElementsByClassName("cart-quantity")[0];
        var price = parseFloat(priceElement.innerText.replace("$", "").replace("MXN", ""));
        var quantity = quantityElement.value;
        total += price * quantity;
    }
    //Si hay centavos en el precio
    total = Math.round(total * 100) / 100;

    document.getElementsByClassName("total-price")[0].innerText = "$" + total.toFixed(2);
}



