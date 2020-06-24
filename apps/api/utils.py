import datetime

from aklub.models import DonorPaymentChannel


def get_or_create_dpch(serializer, profile):
    dpch, created = DonorPaymentChannel.objects.get_or_create(
                    event=serializer.validated_data['event'],
                    money_account=serializer.validated_data['money_account'],
                    user=profile,
                    )
    if created:
        dpch.expected_date_of_first_payment = datetime.date.today() + datetime.timedelta(days=3)
        if serializer.validated_data.get('regular'):
            dpch.regular_payments = 'regular'
        else:
            dpch.regular_payments = 'onetime'
        dpch.regular_amount = serializer.validated_data['amount']
        dpch.generate_VS()
        dpch.save()
    return dpch.VS
