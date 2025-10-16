import './init.js';
import { managerPage, managerRightPage, managerPopup } from './init.js'; // если ты экспортируешь его из init.js

// делаем доступным глобально
window.managerPage = managerPage;
window.managerRightPage = managerRightPage;
window.managerPopup = managerPopup;

function openText (heading, text, buttonText) {
    managerPopup.showExclusive ('fixed');
    const fixedHeading = document.getElementById("fixed_heading");
    const fixedText = document.getElementById("fixed_text");
    const fixedTextButton = document.getElementById("fixed_button");

    fixedHeading.innerHTML = heading;
    fixedText.innerHTML = text;
    fixedTextButton.innerHTML = buttonText;
}

const API_IP = "api.survivilav.ru";
const API_PORT = "8000";
const API_BASE = `https://${API_IP}:${API_PORT}/api`;

function getValue(id) {
  return document.getElementById(id).value.trim();
}

// Очистить все поля
document.getElementById("btn_clear").onclick = () => {
  document.querySelectorAll("input, textarea").forEach(el => el.value = "");
};

// Отправить заявку
document.getElementById("btn_send").onclick = async () => {
  const data = {
    nickname: getValue("nickname"),
    invite: getValue("invite"),
    about: getValue("about"),
    telegram: getValue("telegram"),
    email: getValue("email"),
    source: getValue("source"),
    expectations: getValue("expectations"),
    age: getValue("age"),
  };

  if (!data.nickname && !data.invite) {
    alert("Нужно указать хотя бы ник или приглашение!");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const json = await res.json().catch(() => ({})); // если сервер не вернул JSON

    if (!res.ok) {
      // Сервер вернул ошибку (400, 404, 500 и т.д.)
      const msg = json.detail || json.message || `Ошибка ${res.status}`;
      console.error(`Ошибка ${res.status}:`, msg);
      openText("ОШИБКА", msg, "Понял");
      return;
    }

    // Всё ок
    alert(json.message || "Заявка успешно отправлена!");
    openText("УСПЕХ", json.message || "Заявка успешно отправлена!", "Отлично");

  } catch (err) {
    console.error(err);
    alert("Ошибка соединения с сервером.");
    openText("ОШИБКА", "Ошибка соединения с сервером.", "Понял");
  }
};

// Отменить заявку
document.getElementById("btn_cancel").onclick = async () => {
  const nickname = getValue("nickname");
  if (!nickname) {
    alert("Введите ник для отмены!");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/cancel?nickname=${encodeURIComponent(nickname)}`, {
      method: "POST",
    });

    const json = await res.json().catch(() => ({}));

    if (!res.ok) {
      const msg = json.detail || json.message || `Ошибка ${res.status}`;
      console.error(`Ошибка ${res.status}:`, msg);
      openText("ОШИБКА", msg, "Понял");
      return;
    }

    alert(json.message || "Заявка отменена.");
    openText("УСПЕХ", json.message || "Заявка отменена.", "ОК");

  } catch (err) {
    console.error(err);
    alert("Ошибка соединения с сервером.");
    openText("ОШИБКА", "Ошибка соединения с сервером.", "Понял");
  }
};

