---
comments: true
description: "Learn how to develop the Open Web Calendar."
---

# Setup & Tests

This section guides you through everything you need to know to develop the
software: build it and make changes.

## Clone the Repository

```sh
git clone https://github.com/niccokunzmann/open-web-calendar
cd open-web-calendar
```

## Running the App

1. Optional: Install virtualenv and Python3 and create a virtual environment.

    ```sh
    virtualenv -p python3 ENV
    source ENV/bin/activate
    ```

2. Install the packages.

    ```sh
    pip install -r requirements.txt
    ```

3. Start the app.

    ```sh
    python3 app.py
    ```

You can [configure the app through environment](../host/self.md#environment-variables) variables.

## Running Tests

To run the tests, we use `tox`.
`tox` tests all different Python versions which we want to
be compatible to.

```sh
pip install tox
```

Run all tests:

```sh
tox
```

Run a specific Python version:

```sh
tox -e py39
```

## Browser Testing

We use selenium to test the app in different browsers.
By default, Firefox is used.
You can test the features like this:

```sh
tox -e web
```

If you like to change the browser, use

```sh
tox -e web -- -D browser=firefox
tox -e web -- -D browser=chrome
```

You can also change the layout of the window to test the responsive design:

```sh
tox -e web -- -D window=375x812 # iPhone11 size
```

## Documentation

You can build the documentation with `tox`, too.
It is located in the `docs` directory.

```sh
tox -e docs -- build # ./site
tox -e docs -- serve
```

We are using [mkdocs] with the [material theme](https://squidfunk.github.io/mkdocs-material/).

[web]: https://open-web-calendar.hosted.quelltext.eu/
[mkdocs]: https://www.mkdocs.org
