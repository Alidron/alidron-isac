from .concurrency import green

class Observable(set):

    def __call__(self, *args, **kwargs):
        for observer in self:
            green.spawn(observer, *args, **kwargs)

    def __iadd__(self, observer):
        self.add(observer)
        return self

    def __isub__(self, observer):
        self.remove(observer)
        return self
