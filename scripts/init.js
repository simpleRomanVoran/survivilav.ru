// js/init.js
import Popuper from './popuper.js';

const managerPage = new Popuper();
managerPage.registerMany(["center_main", "center_blog"], "display", "flex");
const managerRightPage = new Popuper();
managerRightPage.registerMany(["right_main", "right_blog"], "display", "flex");
const managerPopup = new Popuper();
managerPopup.registerMany(["fixed"], "display", "block");

managerPage.hideAll();
managerRightPage.hideAll();
managerPopup.hideAll();

managerPage.show("center_main");
managerRightPage.show("right_main");

// Экспортируем, если хотим доступ из консоли/других модулей
export { managerPage, managerRightPage, managerPopup };
