const priceFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

function getSelectedMealsPrice() {
  if (!window.FOOD_PRICES) return 0;

  const mealSelects = document.querySelectorAll(".js-meal-select");
  let mealsPrice = 0;

  mealSelects.forEach((select) => {
    if (select.value !== "1") {
      return;
    }

    mealsPrice += window.FOOD_PRICES[select.dataset.meal] || 0;
  });

  return mealsPrice;
}

function getDurationCoefficient() {
  if (!window.FOOD_PRICES) return 1;

  const durationSelect = document.querySelector("#plan-duration");
  const selectedDuration = durationSelect ? durationSelect.value : "1";

  return window.FOOD_PRICES.coefficients[selectedDuration] || 1;
}

function updateOrderPrice() {
  const priceElement = document.querySelector("#order-price");
  if (!priceElement) {
    return;
  }

  const totalPrice = getSelectedMealsPrice() * getDurationCoefficient();
  priceElement.textContent = `${priceFormatter.format(totalPrice)}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const orderForm = document.querySelector("#order");
  if (!orderForm) {
    return;
  }

  orderForm.addEventListener("change", updateOrderPrice);
  updateOrderPrice();
});
