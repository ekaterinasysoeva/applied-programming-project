from functools import wraps


class LogCall:
    def __init__(self, fn):
        self.fn = fn
        wraps(fn)(self)

    def __call__(self, *args, **kwargs):
        print(f"Calling {self.fn.__name__} with args={args}, kwargs={kwargs}")
        result = self.fn(*args, **kwargs)
        print(f"{self.fn.__name__} returned {result}")
        return result


@LogCall
def say_hello(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(say_hello("Student"))
