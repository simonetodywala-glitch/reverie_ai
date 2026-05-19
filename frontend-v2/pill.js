class Pill {
    constructor(data) {
        this.el = document.createElement('div');
        this.el.id = data.id;
    }

    update(data) {}

    destroy() {
        this.el.remove();
    }
}

function el(tag, className) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    return e;
}