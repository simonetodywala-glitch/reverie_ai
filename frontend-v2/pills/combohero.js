class ComboHeroPill extends Pill {
    constructor(data) {
        super(data);
        this.el.className = 'combohero animable animate';

        const hero = el('div', 'hero');
        const comboText = el('div', 'combo-text');
        this._title = el('p', 'combo-title');
        const comboStats = el('div', 'combo-stats');
        this._statLarge = el('h1', 'combo-stat-large');
        this._statSmall = el('p', 'combo-stat-small');
        this._icon = el('div', 'combo-icon');

        comboStats.append(this._statLarge, this._statSmall);
        comboText.append(this._title, comboStats);
        hero.append(comboText, this._icon);

        this._buttons = el('div', 'combo-buttons');
        this.el.append(hero, this._buttons);

        this.update(data);
    }

    update(data) {
        this._title.textContent = data.title;
        this._statLarge.textContent = data.statLarge;
        this._statSmall.textContent = data.statSmall;

        this._buttons.innerHTML = '';
        data.buttons.forEach(btn => {
            const b = el('button', `btn btn-${btn.style}`);
            b.textContent = btn.label;
            this._buttons.appendChild(b);
        });
    }
}