from django.db.models import DateTimeField

# ! Unfortually doing an expression wrapper with a datetimefield output, i've noticed that the value can be 'null'.
# ! Of cource we are handling this inside filters, however not inside the actual date time field model aswel, therefore I had to create
# ! my own custom date time field to handle None
class CustomDateTimeField(DateTimeField):
    def to_python(self, value):
        print('to_python | value | ', value)
        if value is None or value is 'null':
            return value
        
        return DateTimeField.to_python(value)