def validate_age(func):
    print("validate age starts main decoratoer")
    def func(age: int):
        print("func wrapper starts main decoratoer")

        if age <=18:
            raise ValueError("age must be above 18")

        print("func wrapper returns age",age)

        return func

    print("validte age ends here.")
    return validate_age



@validate_age
def check_age(age):
    print("check comes here ")
    print(age)
    return age


check_age(18)

