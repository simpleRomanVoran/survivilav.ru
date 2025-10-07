class Popup {
    constructor(id, type = "class", option = "block") {
        this.id = id;
        this.type = type;
        this.option = option;
        this.el = document.getElementById(id);

        if (!this.el) {
            console.error(`Popup error: элемент с ID "${id}" не найден`);
        }
    }

    show() {
        if (!this.el) return;

        if (this.type === "class") {
            this.el.classList.remove("popup_hide");
        } else if (this.type === "display") {
            this.el.style.display = this.option;
        } else {
            console.error(`Popup error: неверный type "${this.type}"`);
        }
    }

    hide() {
        if (!this.el) return;

        if (this.type === "class") {
            this.el.classList.add("popup_hide");
        } else if (this.type === "display") {
            this.el.style.display = "none";
        }
    }

    toggle() {
        if (!this.el) return;

        if (this.type === "class") {
            this.el.classList.toggle("popup_hide");
        } else if (this.type === "display") {
            this.el.style.display = 
                this.el.style.display === "none" || !this.el.style.display
                    ? this.option
                    : "none";
        }
    }
}

class Popuper {
    constructor() {
        this.popups = new Map();
    }

    // регистрация одного попапа
    register(id, type = "class", option = "block") {
        const popup = new Popup(id, type, option);
        this.popups.set(id, popup);
        return popup;
    }

    // регистрация нескольких
    registerMany(ids, type = "class", option = "block") {
        ids.forEach(id => this.register(id, type, option));
    }

    get(id) {
        return this.popups.get(id);
    }

    show(id) { this.get(id)?.show(); }
    hide(id) { this.get(id)?.hide(); }
    toggle(id) { this.get(id)?.toggle(); }

    showAll() { this.popups.forEach(p => p.show()); }
    hideAll() { this.popups.forEach(p => p.hide()); }
    toggleAll() { this.popups.forEach(p => p.toggle()); }

    // показать один попап, скрыв все остальные
    showExclusive(id) {
        this.hideAll();
        this.show(id);
    }
}

const managerPage = new Popuper();
managerPage.registerMany(["center_main", "center_blog"], "display", "flex");
const managerRightPage = new Popuper();
managerRightPage.registerMany(["right_main", "right_blog"], "display", "flex");
const managerPopup = new Popuper();
managerPopup.registerMany(["fixed"], "display", "block");

managerPage.hideAll();
managerRightPage.hideAll();
managerPopup.hideAll();
managerPage.show ("center_main")
managerRightPage.show ("right_main")