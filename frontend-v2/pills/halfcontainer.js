class HalfContainerPill extends Pill {
    constructor(data) {
        super(data);
        this.el.className = 'halfcontainer animable animate';
        this.update(data);
    }

    update(data) {
        this.el.innerHTML = '';
        data.items.forEach(item => {
            const half = el('div', 'halfmetric animable animate');
            const title = el('h2', 'half-title');
            const content = el('h2', 'half-content');
            title.textContent = item.title;
            content.textContent = item.content;
            half.append(title, content);
            this.el.appendChild(half);
        });
    }
}