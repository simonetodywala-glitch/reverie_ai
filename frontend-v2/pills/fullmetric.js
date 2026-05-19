class FullMetricPill extends Pill {
    constructor(data) {
        super(data);
        this.el.className = 'fullmetric animable animate';

        const text = el('div', 'full-text');
        this._title = el('h2', 'full-title');
        this._content = el('h2', 'full-content');
        const button = el('div', 'full-button');
        button.textContent = '->';

        text.append(this._title, this._content);
        this.el.append(text, button);

        this.update(data);
    }

    update(data) {
        this._title.textContent = data.title;
        this._content.textContent = data.content;
    }
}