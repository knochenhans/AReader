class Test:
    def __init__(self) -> None:
        test = 0

    def fuck(self):
        self.test = 1
        print(self.test)

test = Test()
test.fuck()