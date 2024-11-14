def fibonacci(n):
    if n < 1:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


response = fibonacci(20)

shared_list = request_read_resource("shared_int_array")
response = 0
for i in range(3):
    response += shared_list[i]
