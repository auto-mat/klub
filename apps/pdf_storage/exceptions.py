from rest_framework.exceptions import APIException


class HasNoPayment(APIException):
    status_code = 404
    default_detail = 'Payment for last month doesnt exist'
    default_code = 'payment_for_last_month_doesnt_exist'


class PdfDoNotExist(APIException):
    status_code = 404
    default_detail = 'PDF doesnt exist'
    default_code = 'pdf_do_not_exixst'
