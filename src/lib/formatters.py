def get_size_readable(size: int, decimals: bool = True) -> str:
    assert size >= 0

    if size < 2**10:
        unit = "B"
        converted = size
    elif size < 2**20:
        unit = "KB"
        converted = (size / (2**10))
    else:
        unit = "MB"
        converted = (size / (2**20))

    if decimals:
        return f"{converted:.2f} {unit}"
    else:
        return f"{int(converted)} {unit}"
