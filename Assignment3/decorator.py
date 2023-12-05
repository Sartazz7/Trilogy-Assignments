
def validate_divide(func):
    def inner_func(*args, **kwargs):
        try:
            a = float(args[0])
            b = float(args[1])
            print(f'The arguments of the divide function are {args[0]} and {args[1]}.')
            c = func(*args,**kwargs)
            return c
        except Exception as e:
            print(f'The arguments {args[0]} and {args[1]} are invalid for divide function.')
            print(e)
    return inner_func

@validate_divide
def divide(a, b):
    return a/b

print(f'The output after division is {divide(4,2)}\n')
print(f'The output after division is {divide("4",2)}\n')