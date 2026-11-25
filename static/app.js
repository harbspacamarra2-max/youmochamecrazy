// app.js
// This file makes the ORDER SCREEN work:
// choosing a category, adding items, changing the quantity, the total, Clear, and Pay.

// The current order. Each item looks like:
// { id: "2", name: "Cafe Latte", price: 140, quantity: 2 }
var order = [];

// Parts of the page that we will change
var orderList    = document.getElementById('orderList');
var emptyMessage = document.getElementById('emptyMessage');
var totalText    = document.getElementById('total');
var payButton    = document.getElementById('payButton');
var clearButton  = document.getElementById('clearButton');
var message      = document.getElementById('message');


// ----- CATEGORY TABS -----
// Show only the items of the chosen category (Coffee, Non Coffee, or Pastry)
function showCategory(category) {
  var tabs = document.querySelectorAll('.tab');
  for (var i = 0; i < tabs.length; i++) {
    if (tabs[i].dataset.category === category) {
      tabs[i].classList.add('active');
    } else {
      tabs[i].classList.remove('active');
    }
  }

  var items = document.querySelectorAll('.item');
  for (var j = 0; j < items.length; j++) {
    if (items[j].dataset.category === category) {
      items[j].style.display = '';       // show
    } else {
      items[j].style.display = 'none';   // hide
    }
  }
}


// ----- ADD AN ITEM -----
// Runs when the cashier taps a menu card
function addItem(card) {
  // If the item is already in the order, just add 1 to its quantity
  for (var i = 0; i < order.length; i++) {
    if (order[i].id === card.dataset.id) {
      order[i].quantity = order[i].quantity + 1;
      showOrder();
      return;
    }
  }

  // If it is a new item, add it to the order with quantity 1
  order.push({
    id: card.dataset.id,
    name: card.dataset.name,
    price: Number(card.dataset.price),
    quantity: 1
  });
  showOrder();
}


// ----- CHANGE THE QUANTITY -----
// change is +1 when the cashier presses "+" and -1 when they press "-"
function changeQuantity(index, change) {
  order[index].quantity = order[index].quantity + change;

  // If the quantity becomes 0, remove the item from the order
  if (order[index].quantity <= 0) {
    order.splice(index, 1);
  }
  showOrder();
}


// ----- COMPUTE THE TOTAL -----
// Total = (price x quantity) of every item added together
function computeTotal() {
  var total = 0;
  for (var i = 0; i < order.length; i++) {
    total = total + order[i].price * order[i].quantity;
  }
  return total;
}


// ----- SHOW THE ORDER ON THE RIGHT SIDE -----
function showOrder() {
  orderList.innerHTML = '';   // clear the old list first

  for (var i = 0; i < order.length; i++) {
    var item = order[i];
    var row = document.createElement('div');
    row.className = 'order-item';
    row.innerHTML =
      '<div>' +
        '<div class="oi-name">' + item.name + '</div>' +
        '<div class="oi-price">PHP ' + (item.price * item.quantity) + '</div>' +
      '</div>' +
      '<div class="qty">' +
        '<button class="q-btn minus" onclick="changeQuantity(' + i + ', -1)">-</button>' +
        '<span>' + item.quantity + '</span>' +
        '<button class="q-btn plus" onclick="changeQuantity(' + i + ', 1)">+</button>' +
      '</div>';
    orderList.appendChild(row);
  }

  // Show "No items yet" only when the order is empty
  if (order.length === 0) {
    emptyMessage.style.display = 'block';
    payButton.disabled = true;     // cannot pay an empty order
  } else {
    emptyMessage.style.display = 'none';
    payButton.disabled = false;
  }

  totalText.textContent = 'PHP ' + computeTotal().toLocaleString();
}


// ----- CLEAR THE ORDER -----
function clearOrder() {
  order = [];
  showOrder();
}


// ----- SHOW A SHORT MESSAGE AT THE BOTTOM -----
function showMessage(text, isError) {
  message.textContent = text;
  message.className = isError ? 'toast show error' : 'toast show';
  setTimeout(function () {
    message.className = 'toast';   // hide it after 3 seconds
  }, 3000);
}


// ----- PAY -----
// Sends the order to the server, which saves it in the database
function pay() {
  // Prepare the list of items to send (product id and quantity only)
  var itemsToSend = [];
  for (var i = 0; i < order.length; i++) {
    itemsToSend.push({ product_id: order[i].id, quantity: order[i].quantity });
  }

  payButton.disabled = true;   // stop double clicking while saving

  fetch('/pay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items: itemsToSend })
  })
    .then(function (response) { return response.json(); })
    .then(function (result) {
      if (result.ok) {
        showMessage('Order #' + result.order_id + ' paid. Total PHP ' + result.total.toLocaleString(), false);
        clearOrder();   // ready for the next customer
      } else {
        showMessage(result.message, true);
        payButton.disabled = false;
      }
    })
    .catch(function () {
      showMessage('Payment failed. Please try again.', true);
      payButton.disabled = false;
    });
}


// ----- CONNECT THE BUTTONS -----
var tabs = document.querySelectorAll('.tab');
for (var t = 0; t < tabs.length; t++) {
  tabs[t].onclick = function () { showCategory(this.dataset.category); };
}

var cards = document.querySelectorAll('.item');
for (var c = 0; c < cards.length; c++) {
  cards[c].onclick = function () { addItem(this); };
}

clearButton.onclick = clearOrder;
payButton.onclick = pay;

// When the page opens: show the Coffee tab and an empty order
showCategory('Coffee');
showOrder();
