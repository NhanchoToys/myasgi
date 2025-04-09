# /                 -> Exact("/")
# /foo              -> Exact("/foo")
# /foo/             -> Exact("/foo/")
# /foo/bar          -> Exact("/foo/bar")
# /foo/bar/{n}      -> Exact("/foo/bar/"), Format("n")
# /foo/{n}/bar      -> Exact("/foo/"), Format("n"), Exact("/bar")
# /foo{n:5}/bar     -> Exact("/foo"), Format("n", minl=5, maxl=5), Exact("/bar")
# /foo/{m:1-}/{n:3-5}bar -> Exact("/foo/"), Format("m", minl=1, maxl=-1), Exact("/"), Format("n", minl=3, maxl=5), Exact("bar")
# /*                -> Exact("/"), Format("_")
# /foo/*bar         -> Exact("/foo/"), Format("_"), Exact("bar")
# /foo/*/bar        -> Exact("/foo/"), Format("_"), Exact("/bar")
# /foo/**/bar       -> Exact("/foo/"), Format("_", ignore_sep=True), Exact("/bar")

# ["foo", Format("m", minl=1, maxl=-1), [Format("n", minl=3, maxl=5), "bar"], "*"]


import ctypes

dll = ctypes.CDLL("./c_route.so")
dll.parse_route.restype = type("c_char_alloc", (ctypes.c_char_p,), {})
dll.free_parsed_route.argtypes = (ctypes.c_void_p,)
dll.free_parsed_route.restype = None


def compile_route(pattern: str) -> list[bytes]:
    if pattern[0] != "/":
        from app.exceptions import ParseError
        raise ParseError("The first character in route pattern must be '/'.")

    # res: list[str] = []
    # for path in pattern[1:].split("/"):
    #     if (star_idx := path.find("*")) != -1:
    #         path = "".join((path[:star_idx], "{_}", path[star_idx + 1:]))
    #     if "{" not in path and "}" not in path and "*" not in path:
    #         res.append(path)

    outlen = ctypes.c_size_t()
    data = pattern[1:].encode()
    ret = dll.parse_route(data, len(data), ctypes.byref(outlen))
    res = ctypes.string_at(ret, outlen.value - 2).split(b"\x01")
    dll.free_parsed_route(ret)

    return res


if __name__ == "__main__":
    print(compile_route("/foo/{n:5}foo/bar/**/baz"))
    print(compile_route("/"))
