from rest_framework.exceptions import APIException


class DonorPaymentChannelDoesntExist(APIException):
    status_code = 404
    default_detail = 'Donor payment Channel with this event/money_account/VS doesnt exist'
    default_code = 'dpch_doesnt_exist'
