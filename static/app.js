// app.js
// This file makes the ORDER SCREEN work:
// categories, drink options, the order list, discounts, payment, and the Pay button.

// The current order. Each item looks like:
// { key: "2-1-5", id: "2", name: "Cafe Latte", options: "16oz, Iced", optionIds: [2, 5], price: 160, quantity: 1 }
var order = [];

// The drink being chosen in the options pop-up
var chosenCard = null;

// Parts of the page that we will read or change
var orderList      = document.getElementById('orderList');
var emptyMessage   = document.getElementById('emptyMessage');
var payButton      = document.getElementById('payButton');
var message        = document.getElementById('message');
var customerName   = document.getElementById('customerName');
var discountType   = document.getElementById('discountType');
var discountId     = document.getElementById('discountId');
var cashReceived   = document.getElementById('cashReceived');
var cashRow        = document.getElementById('cashRow');
var optionsBox     = document.getElementById('optionsBox');


// ----- SMALL HELPERS -----
// Show a number as money, for example 1234.5 becomes "PHP 1,234.50"
function peso(amount) {
  return 'PHP ' + amount.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Get the chosen value of a group of toggle buttons (order type or payment method)
function chosenToggle(groupId) {
  return document.querySelector('#' + groupId + ' .toggle-btn.active').dataset.value;
}

// Show a short message at the bottom for 3 seconds
function showMessage(text) {
  message.textContent = text;
  message.className = 'toast show error';
  setTimeout(function () { message.className = 'toast'; }, 3000);
}


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


// ----- TAPPING A MENU CARD -----
// Drinks open the options pop-up. Pastries are added right away.
function tapItem(card) {
  if (card.dataset.drink === '1') {
    openOptions(card);
  } else {
    addToOrder(card.dataset.id, card.dataset.name, Number(card.dataset.price), '', []);
  }
}


// ----- DRINK OPTIONS POP-UP -----
function openOptions(card) {
  chosenCard = card;
  document.getElementById('optionsTitle').textContent = card.dataset.name;
  document.getElementById('optionsPrice').textContent = 'Starts at ' + peso(Number(card.dataset.price));

  // Reset the choices: 12oz, Hot, and no add-ons
  var inputs = optionsBox.querySelectorAll('input');
  for (var i = 0; i < inputs.length; i++) {
    inputs[i].checked = false;
  }
  optionsBox.querySelector('input[name="Size"]').checked = true;
  optionsBox.querySelector('input[name="Temperature"]').checked = true;

  optionsBox.classList.add('show');
}

function closeOptions() {
  optionsBox.classList.remove('show');
  chosenCard = null;
}

// Add the drink with the chosen options to the order
function addWithOptions() {
  var price = Number(chosenCard.dataset.price);
  var names = [];
  var ids = [];

  var checked = optionsBox.querySelectorAll('input:checked');
  for (var i = 0; i < checked.length; i++) {
    price = price + Number(checked[i].dataset.extra);   // add the extra price of each option
    names.push(checked[i].dataset.name);
    ids.push(Number(checked[i].value));
  }

  addToOrder(chosenCard.dataset.id, chosenCard.dataset.name, price, names.join(', '), ids);
  closeOptions();
}


// ----- ADD AN ITEM TO THE ORDER -----
function addToOrder(id, name, price, options, optionIds) {
  // The same drink with the same options is counted on one line
  var key = id + '-' + optionIds.join('-');

  for (var i = 0; i < order.length; i++) {
    if (order[i].key === key) {
      order[i].quantity = order[i].quantity + 1;
      showOrder();
      return;
    }
  }

  order.push({ key: key, id: id, name: name, options: options, optionIds: optionIds, price: price, quantity: 1 });
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


// ----- COMPUTE THE TOTALS -----
// Menu prices already include 12% VAT.
// Senior Citizens and PWDs get 20% off the price without VAT, and pay no VAT.
function computeTotals() {
  var subtotal = 0;
  for (var i = 0; i < order.length; i++) {
    subtotal = subtotal + order[i].price * order[i].quantity;
  }

  var vat, discount, total;
  if (discountType.value === 'None') {
    vat = subtotal - subtotal / 1.12;
    discount = 0;
    total = subtotal;
  } else {
    var priceWithoutVat = subtotal / 1.12;
    vat = subtotal - priceWithoutVat;          // this VAT is removed
    discount = priceWithoutVat * 0.20;
    total = priceWithoutVat - discount;
  }

  return {
    subtotal: subtotal,
    vat: Math.round(vat * 100) / 100,
    discount: Math.round(discount * 100) / 100,
    total: Math.round(total * 100) / 100
  };
}


// ----- SHOW THE ORDER AND THE TOTALS -----
function showOrder() {
  orderList.innerHTML = '';   // clear the old list first

  for (var i = 0; i < order.length; i++) {
    var item = order[i];
    var row = document.createElement('div');
    row.className = 'order-item';
    row.innerHTML =
      '<div>' +
        '<div class="oi-name"></div>' +
        '<div class="oi-options"></div>' +
        '<div class="oi-price">' + peso(item.price * item.quantity) + '</div>' +
      '</div>' +
      '<div class="qty">' +
        '<button class="q-btn minus" onclick="changeQuantity(' + i + ', -1)">-</button>' +
        '<span>' + item.quantity + '</span>' +
        '<button class="q-btn plus" onclick="changeQuantity(' + i + ', 1)">+</button>' +
      '</div>';
    row.querySelector('.oi-name').textContent = item.name;
    row.querySelector('.oi-options').textContent = item.options;
    orderList.appendChild(row);
  }

  emptyMessage.style.display = order.length === 0 ? 'block' : 'none';

  // Show the totals
  var totals = computeTotals();
  document.getElementById('subtotal').textContent = peso(totals.subtotal);
  document.getElementById('total').textContent = peso(totals.total);

  if (discountType.value === 'None') {
    document.getElementById('vatLabel').textContent = 'VAT (12%, included)';
    document.getElementById('vat').textContent = peso(totals.vat);
    document.getElementById('discount').textContent = peso(0);
  } else {
    document.getElementById('vatLabel').textContent = 'Less VAT (12%)';
    document.getElementById('vat').textContent = '-' + peso(totals.vat);
    document.getElementById('discount').textContent = '-' + peso(totals.discount);
  }

  // Cash payments show the cash received and the change
  var isCash = chosenToggle('paymentMethod') === 'Cash';
  cashRow.style.display = isCash ? '' : 'none';
  var change = Number(cashReceived.value) - totals.total;
  document.getElementById('change').textContent = peso(isCash && change > 0 ? change : 0);

  // The Pay button only works when there are items, and enough cash for cash payments
  var enoughCash = !isCash || Number(cashReceived.value) >= totals.total;
  payButton.disabled = order.length === 0 || !enoughCash;
}


// ----- CLEAR THE ORDER -----
function clearOrder() {
  order = [];
  customerName.value = '';
  discountType.value = 'None';
  discountId.value = '';
  discountId.disabled = true;
  cashReceived.value = '';
  showOrder();
}


// ----- PAY -----
// Sends the order to the server. If it is saved, the receipt opens.
function pay() {
  if (discountType.value !== 'None' && discountId.value.trim() === '') {
    showMessage('Please enter the Senior Citizen or PWD ID number.');
    return;
  }

  // Prepare the items to send (product id, quantity, and chosen options)
  var itemsToSend = [];
  for (var i = 0; i < order.length; i++) {
    itemsToSend.push({ product_id: order[i].id, quantity: order[i].quantity, option_ids: order[i].optionIds });
  }

  payButton.disabled = true;   // stop double clicking while saving

  fetch('/pay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items: itemsToSend,
      customer_name: customerName.value,
      order_type: chosenToggle('orderType'),
      discount_type: discountType.value,
      discount_id_no: discountId.value,
      payment_method: chosenToggle('paymentMethod'),
      amount_paid: cashReceived.value
    })
  })
    .then(function (response) { return response.json(); })
    .then(function (result) {
      if (result.ok) {
        window.location = '/receipt/' + result.order_id;   // open the receipt
      } else {
        showMessage(result.message);
        payButton.disabled = false;
      }
    })
    .catch(function () {
      showMessage('Payment failed. Please try again.');
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
  cards[c].onclick = function () { tapItem(this); };
}

// Toggle buttons: only one can be chosen in each group
var toggleButtons = document.querySelectorAll('.toggle-btn');
for (var b = 0; b < toggleButtons.length; b++) {
  toggleButtons[b].onclick = function () {
    var siblings = this.parentElement.querySelectorAll('.toggle-btn');
    for (var s = 0; s < siblings.length; s++) {
      siblings[s].classList.remove('active');
    }
    this.classList.add('active');
    showOrder();
  };
}

// The ID number box is only used when there is a discount
discountType.onchange = function () {
  discountId.disabled = discountType.value === 'None';
  if (discountId.disabled) { discountId.value = ''; }
  showOrder();
};

cashReceived.oninput = showOrder;
document.getElementById('clearButton').onclick = clearOrder;
document.getElementById('cancelOptions').onclick = closeOptions;
document.getElementById('addWithOptions').onclick = addWithOptions;
payButton.onclick = pay;

// When the page opens: show the Coffee tab and an empty order
showCategory('Coffee');
showOrder();
