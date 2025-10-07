// js/popuper.js
import Popup from './popup.js';

export default class Popuper {
    constructor() {
        this.popups = new Map();
    }

    register(id, type = "class", option = "block") {
        const popup = new Popup(id, type, option);
        this.popups.set(id, popup);
        return popup;
    }

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

    showExclusive(id) {
        this.hideAll();
        this.show(id);
    }
}
