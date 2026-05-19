// The ViewModel class manages state.

class ViewModel {

    // The ViewModel holds the state.

    #state = {
        screen: 'home',
        screenData: [],
    };

    // The ViewModel suggests that the state be accessed through its getter.
    
    get state() {
        return this.#state;
    }

    // The View can hook onto the ViewModel.

    #subscribers = [];

    // The ViewModel notifies its subscribers when the state changes.

    subscribe(fn) {
        // The function is added to the list of subscribers.
        this.#subscribers.push(fn);
        return () => {
            // This function allows the object to unsubscribe (be removed from the list of subscribers) from the ViewModel.
            this.#subscribers = this.#subscribers.filter(s => s !== fn);
        };
    }

    // The ViewModel notifies its subscribers by running the given function and passing the state.

    #notify() {
        this.#subscribers.forEach(fn => fn(this.#state));
    }

    // The ViewModel provides a way to navigate to a new screen.

    navigate(screen, data = {}) {
        this.#state.screen = screen;
        this.#state.screenData = data;
        this.#notify();
    }

    // The ViewModel provides a way to update the data for the current screen.
    
    setScreenData(data) {
        this.#state.screenData = data;
        this.#notify();
    }
}

// One ViewModel, please!

const vm = new ViewModel();