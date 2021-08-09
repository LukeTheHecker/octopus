
def printDecorator(fn):
    def wrapper(*args, **kwargs):
        print("Startig function:")
        fn(*args, **kwargs)
        print("function is finished.")
    return wrapper

@printDecorator
def square(number):
    return number**2

number = 2
print(square(number))

