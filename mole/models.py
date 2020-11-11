from django.db import models


class User(models.Model):
    name = models.CharField(max_length=200)
    isMole = models.BooleanField(default=False)


class Evidence(models.Model):
    Name = models.CharField(max_length=200)
    isTrue = models.BooleanField(default=True)  # optional
    finder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='finder', default=1)  
    sharedWith = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    TYPES_OF_EVIDENCE = [
        ('W', 'Weapon'),
        ('L', 'Location'),
        ('P', 'Person'),
        ('S', 'Statement'),
    ]
    evidence_type = models.CharField(
        max_length=2,
        choices=TYPES_OF_EVIDENCE,
        default=TYPES_OF_EVIDENCE[2],
    )

    def __init__(self, name, evidence_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.evidence_type = evidence_type


class Event(models.Model):
    Name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    initiated_at = models.DateTimeField(auto_now_add=True, blank=True)
    result_received = models.DateTimeField()
    result = models.IntegerField()  # maybe factor

    def __init__(self, name, description, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.description = description
        self.result = -404
