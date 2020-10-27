from rest_framework.exceptions import APIException


class EmailDoesntExist(APIException):
    status_code = 404
    default_detail = 'Email Does not exist'
    default_code = 'email_doesnt_exist'


class DonorPaymentChannelDoesntExist(APIException):
    status_code = 404
    default_detail = 'Donor payment Channel with this event/money_account/VS doesnt exist'
    default_code = 'dpch_doesnt_exist'


class PaymentsDoesntExist(APIException):
    status_code = 404
    default_detail = 'Payment since registered payment + 14 days doesnt exist '
    default_code = 'payment_doesnt_exist'


class PasswordsDoNotMatch(APIException):
    status_code = 404
    default_detail = 'Passoword 1 and 2 doesnt match'
    default_code = 'password_no_match'
