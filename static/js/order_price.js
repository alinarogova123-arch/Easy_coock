const MEAL_PRICES = {
  breakfast: 200,
  lunch: 300,
  dinner: 400,
  dessert: 100,
};

const DURATION_COEFFICIENTS = {
  1: 1,
  3: 1.6,
  6: 1.8,
  12: 2,
};

const priceFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

function getSelectedMealsPrice() {
  const mealSelects = document.querySelectorAll(".js-meal-select");
  let mealsPrice = 0;

  mealSelects.forEach((select) => {
    if (select.value !== "1") {
      return;
    }

    mealsPrice += MEAL_PRICES[select.dataset.meal] || 0;
  });

  return mealsPrice;
}

function getDurationCoefficient() {
  const durationSelect = document.querySelector("#plan-duration");
  const selectedDuration = durationSelect ? durationSelect.value : "1";

  return DURATION_COEFFICIENTS[selectedDuration] || DURATION_COEFFICIENTS[1];
}

function updateOrderPrice() {
  const priceElement = document.querySelector("#order-price");
  if (!priceElement) {
    return;
  }

  const totalPrice = getSelectedMealsPrice() * getDurationCoefficient();
  priceElement.textContent = `${priceFormatter.format(totalPrice)} ₽`;
}

document.addEventListener("DOMContentLoaded", () => {
  const orderForm = document.querySelector("#order");
  if (!orderForm) {
    return;
  }

  orderForm.addEventListener("change", updateOrderPrice);
  updateOrderPrice();
});
