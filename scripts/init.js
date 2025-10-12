// js/init.js
import Popuper from './popuper.js';

const managerPage = new Popuper();
managerPage.registerMany(["center_main", "center_request", "center_rule", "center_project", "center_account", "center_contact"], "display", "flex");
const managerRightPage = new Popuper();
managerRightPage.registerMany(["right_main", "right_request", "right_rule", "right_project", "right_account", "right_contact"], "display", "flex");
const managerPopup = new Popuper();
managerPopup.registerMany(["fixed"], "display", "block");

managerPage.hideAll();
managerRightPage.hideAll();
managerPopup.hideAll();

managerPage.show("center_main");
managerRightPage.show("right_main");

// Экспортируем, если хотим доступ из консоли/других модулей
export { managerPage, managerRightPage, managerPopup };
