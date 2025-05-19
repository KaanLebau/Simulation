class Tool:
    def __init__(self, life, replacement_duration, current=None):
        self.life = life
        self.current = current if current is not None else life
        self.replacement_duration = replacement_duration

    def get_life(self):
        return self.current

    def use(self):
        if self.current > 0:
            self.current -= 1
        else:
            raise ValueError('Tools are worn out')

    def is_worn_out(self):
        return self.current <= 0

    def replace(self):
        if self.is_worn_out():
            self.current = self.life

    def get_replacement_duration(self):
        return self.replacement_duration

    def __str__(self):
        return f"life: {self.life}, current: {self.current}, replacement_duration: {self.replacement_duration}"

    def __eq__(self, other):
        if isinstance(other, Tool):
            return self.life == other.life and self.replacement_duration == other.replacement_duration and self.current == other.current and self.replacement_duration == other.replacement_duration
        return False
