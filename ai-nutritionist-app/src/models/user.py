class User:
    def __init__(self, height, weight, sex, age, target_weight):
        self.height = height
        self.weight = weight
        self.sex = sex
        self.age = age
        self.target_weight = target_weight

    def update_weight(self, new_weight):
        self.weight = new_weight

    def update_target_weight(self, new_target_weight):
        self.target_weight = new_target_weight

    def update_personal_info(self, height=None, weight=None, sex=None, age=None):
        if height is not None:
            self.height = height
        if weight is not None:
            self.weight = weight
        if sex is not None:
            self.sex = sex
        if age is not None:
            self.age = age

    def get_user_info(self):
        return {
            "height": self.height,
            "weight": self.weight,
            "sex": self.sex,
            "age": self.age,
            "target_weight": self.target_weight
        }