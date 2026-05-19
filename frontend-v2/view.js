const pillClasses = {
    fullmetric: FullMetricPill,
    halfcontainer: HalfContainerPill,
    combohero: ComboHeroPill,
};

class View {
    #activePills = new Map();

    constructor(vm) {
        vm.subscribe(state => this.#render(state));
    }

    #render(state) {
        const screens = { home: data => this.#renderHome(data) };
        screens[state.screen]?.(state.screenData);
    }

    #renderHome(data) {
        const content = document.querySelector('.content');
        const seen = new Set();

        data.forEach((pill, i) => {
            seen.add(pill.id);
            if (this.#activePills.has(pill.id)) {
                this.#activePills.get(pill.id).update(pill);
            } else {
                const instance = new pillClasses[pill.type](pill);
                this.#activePills.set(pill.id, instance);
                content.appendChild(instance.el);
            }

            const instance = this.#activePills.get(pill.id);
            if (content.children[i] !== instance.el) {
                content.insertBefore(instance.el, content.children[i]);
            }
        });

        this.#activePills.forEach((instance, id) => {
            if (!seen.has(id)) {
                instance.destroy();
                this.#activePills.delete(id);
            }
        });
    }
}

const view = new View(vm);