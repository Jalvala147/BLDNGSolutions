// Carrito 
let cartIcon = document.querySelector("#cart-icon");
let cart = document.querySelector(".cart");
let closeCart = document.querySelector("#close-cart");

// Select para elegir entre Compra o Renta
let purchaseOption = document.getElementById("purchase-option");

// Agregar evento de cambio al select
purchaseOption.addEventListener("change", function () {
    updateCartPrices(); // Llamar a una función para actualizar los precios en el carrito
});

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
    var weeksInputs = document.getElementsByClassName("cart-weeks");
    for (var i = 0; i < weeksInputs.length; i++) {
        var input = weeksInputs[i];
        input.addEventListener("change", weeksChanged);
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
        // Obtener los detalles de las máquinas en el carrito de la función updateTotal()
        var total = updateTotal();

        // Obtener la información de las máquinas de la función updateTotal()
        var cartMachineIdsField = document.getElementById("cart-machine-ids");
        var cartWeeksField = document.getElementById("cart_weeks");

        // Actualizar los campos ocultos
        cartMachineIdsField.value = cartMachineIdsField.value;
        cartWeeksField.value = cartWeeksField.value;
        cartTotalField.value = total.toFixed(2);

        // Enviar el formulario
        document.getElementById("purchase-form").submit();
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
function weeksChanged(event) {
    var input = event.target;
    if (isNaN(input.value) || input.value <= 0) {
        input.value = 1;
    }
    updateTotal();
}

// Variable para almacenar la opción de compra del primer producto agregado
var firstProductOption = null;

//Función para agregar al carrito
function addCartClicked(event) {
    var button = event.target;
    var shopProducts = button.parentElement;
    var title = shopProducts.getElementsByClassName("product-title")[0].innerText;
    var productImg = shopProducts.getElementsByClassName("product-img")[0].src;
    var machineId = shopProducts.getElementsByClassName("machine-id")[0].innerText;
    var selectedOption = purchaseOption.value; // Obtener la opción de compra seleccionada
    
    // Verificar si el carrito está vacío
    var cartContent = document.getElementsByClassName("cart-content")[0];
    if (cartContent.children.length === 0) {
        firstProductOption = null; // Reiniciar la variable si el carrito está vacío
    }
    
    // Verificar si es el primer producto agregado
    if (firstProductOption === null) {
        // Almacena la opción de compra del primer producto
        firstProductOption = selectedOption;
    } else {
        // Si no es el primer producto, verifica si la opción coincide con la del primer producto
        if (selectedOption !== firstProductOption) {
            alert("No puedes mezclar compras con rentas en el carrito.");
            return;
        }
    }

    

    var type = selectedOption === "renta" ? 1 : 0;

    if (selectedOption === "renta") {
        // En la opción de "renta," utiliza la función addProductToCart
        var price = shopProducts.getElementsByClassName("price")[0].innerText;
        addProductToCart(title, price, productImg, machineId, type);
    } else if (selectedOption === "compra") {
        // En la opción de "compra," utiliza la función updateCartForBuy
        updateCartForBuy(title, productImg, machineId, type);
    }

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
function addProductToCart(title, price, productImg, machineId, type) {
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

    // Elige el precio correcto según la opción de compra
    var selectedOption = purchaseOption.value;
    var chosenPrice = selectedOption === "renta" ? price : sell_price;

    var cartBoxContent = `
        <img src="${productImg}" alt="" class="cart-img">
        <!-- Contenido de la caja -->
        <input type="hidden" class="cart-machine-id" value="${machineId}">
        <input type="hidden" class="cart-type" value="${type}">
        <div class="detail-box">
            <div class="cart-product-title">${title}</div>
            <div class="cart-product-id">ID: ${machineId}</div> 
            <div class="cart-price">${chosenPrice}</div>
            <input type="number" value="1" min="1" max="4" class="cart-weeks" id="cart-weeks">
            <span>semanas</span>
        </div>
        <!--borrar carrito-->
        <i class="bx bxs-trash-alt cart-remove"></i>`;
    cartShopBox.innerHTML = cartBoxContent;
    cartItems.appendChild(cartShopBox);
    cartShopBox.getElementsByClassName("cart-remove")[0].addEventListener("click", removeCartItem);
    cartShopBox.getElementsByClassName("cart-weeks")[0].addEventListener("change", weeksChanged);
}



function updateCartForBuy(title, productImg, machineId, type) {
    var sellPriceElement = document.querySelector(`.product-box[data-machine-id="${machineId}"] .sell_price`);
    var sellPrice = parseFloat(sellPriceElement.getAttribute("data-price-compra"));

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

    // Para "Compra," establece el precio en sellPrice y deja el campo de semanas en blanco (null)
    var chosenPrice = sellPrice;
    var weeksDisabled = true;

    var cartBoxContent = `
        <img src="${productImg}" alt="" class="cart-img">
        <!-- Contenido de la caja -->
        <input type="hidden" class="cart-machine-id" value="${machineId}">
        <input type="hidden" class="cart-type" value="${type}">
        <div class="detail-box">
            <div class="cart-product-title">${title}</div>
            <div class="cart-product-id">ID: ${machineId}</div> 
            <div class="cart-price">$${chosenPrice}.00 MXN</div>
            <input type="number" value="0" class="cart-weeks" id="cart-weeks" ${weeksDisabled ? "disabled" : ""}>
        </div>
        <!--borrar carrito-->
        <i class="bx bxs-trash-alt cart-remove"></i>`;
    cartShopBox.innerHTML = cartBoxContent;
    cartItems.appendChild(cartShopBox);
    cartShopBox.getElementsByClassName("cart-remove")[0].addEventListener("click", removeCartItem);
    cartShopBox.getElementsByClassName("cart-weeks")[0].addEventListener("change", weeksChanged);
}




function updateTotal() {
    var cartContent = document.getElementsByClassName("cart-content")[0];
    var cartBoxes = cartContent.getElementsByClassName("cart-box");
    var total = 0;

    // Crear un objeto para almacenar las semanas y los precios de cada máquina en el carrito
    var machineInfo = {};

    for (var i = 0; i < cartBoxes.length; i++) {
        var cartBox = cartBoxes[i];
        var priceElement = cartBox.getElementsByClassName("cart-price")[0];
        var weeksElement = cartBox.getElementsByClassName("cart-weeks")[0];
        var machineIdElement = cartBox.getElementsByClassName("cart-machine-id")[0];
        var titleElement = cartBox.getElementsByClassName("cart-product-title")[0];
        var typeElement = cartBox.getElementsByClassName("cart-type")[0];
        var price = parseFloat(priceElement.innerText.replace("$", "").replace("MXN", ""));
        var weeks = parseInt(weeksElement.value); // Convierte la cantidad de semanas a un número entero
        var machineId = machineIdElement.value;
        var type = typeElement.value; 
        var title = titleElement.innerText;

        // Calcular el precio total para esta máquina y semanas
        var machinePrice = 0;

        if (weeks === 0) {
            // Si semanas es 0, simplemente tomar el precio sin descuento, para compra
            machinePrice = price;
        } else if (weeks === 1) {
            machinePrice = price;
        } else if (weeks === 2) {
            machinePrice = (price * 2) - ((price * 2) * 0.04);
        } else if (weeks === 3) {
            machinePrice = (price * 3) - ((price * 3) * 0.08);
        } else if (weeks === 4) {
            machinePrice = (price * 4) - ((price * 4) * 0.12);
        }

        // Agregar la información de la máquina al objeto
        machineInfo[machineId] = {
            title: title,
            weeks: weeks,
            price: machinePrice,
            type: type
        };

        // Agregar el precio de esta máquina al total
        total += machinePrice;
    }

    // Si hay centavos en el precio
    total = Math.round(total * 100) / 100;

    document.getElementsByClassName("total-price")[0].innerText = "$" + total.toFixed(2);

    // Mostrar detalles de cada máquina en la consola
    for (var machineId in machineInfo) {
        var machineData = machineInfo[machineId];
        console.log("Máquina ID:", machineId);
        console.log("Producto:", machineData.title);
        console.log("Semanas:", machineData.weeks);
        console.log("Precio:", machineData.price);
        console.log("Tipo:", machineData.type);
    }

    // Actualizar el valor del campo oculto
    var cartTotalField = document.getElementById("cart_total");
    var cartWeeksField = document.getElementById("cart_weeks");

    // Convierte el objeto machineInfo en una cadena JSON para almacenarlo en el campo oculto
    var machineInfoJSON = JSON.stringify(machineInfo);

    cartTotalField.value = total.toFixed(2);
    cartWeeksField.value = machineInfoJSON;

    console.log("Total:", cartTotalField.value);
    console.log("Informacion del pedido:", cartWeeksField.value);
}




function weeksChanged(event) {
    var input = event.target;
    if (isNaN(input.value) || input.value <= 0) {
        input.value = 1;
    }
    updateTotal(); // Agrega esta línea para llamar a updateTotal
    console.log("Valor de semanas:", input.value); // Agrega esta línea para depurar
}

//Función para actualizar los precios en el carrito
function updateCartPrices() {
    // Obtener la opción de compra seleccionada
    var selectedOption = purchaseOption.value;

    // Obtener todos los elementos de precio en el carrito
    var cartPrices = document.getElementsByClassName("cart-price");

    // Iterar a través de los elementos de precio y actualizar según la opción
    for (var i = 0; i < cartPrices.length; i++) {
        var cartPrice = cartPrices[i];
        var parentBox = cartPrice.parentElement;
        var machineId = parentBox.getElementsByClassName("cart-machine-id")[0].value;

        // Obtener el precio actual del producto
        var currentPrice = parseFloat(cartPrice.innerText.replace("$", ""));

        // Elegir el precio correcto según la opción de compra
        var chosenPrice = selectedOption === "renta" ? price : sell_price;

        // Actualizar el precio en el carrito
        cartPrice.innerText = "$" + chosenPrice.toFixed(2);

        // Llamar a updateTotal para actualizar el total del carrito
        updateTotal();
    }
}
