import './init.js';
import { managerPage, managerRightPage, managerPopup } from './init.js'; // если ты экспортируешь его из init.js

window.managerPage = managerPage; // делаем доступным глобально
window.managerRightPage = managerRightPage;
window.managerPopup = managerPopup;
