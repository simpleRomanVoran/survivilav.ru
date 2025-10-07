// js/popup.js
export default class Popup {
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
